from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
import os
import time
from typing import Dict, Optional

import numpy as np
import pandas as pd


# Default number of threads to use in torch if os.cpu_count() is unavailable
# and no value is specified.
defaultNumThreads = os.cpu_count() or 8

# Store the timestamp at which the constants module is initialized.  Note
# that module initialization occurs only once regardless of how many times
# the module is imported (see link below).  Storing a designated timestamp
# as a constant allow us to:
#  -Use a consistent notion of "now" throughout scorer execution.
#  -Overwrite "now" when system testing to reduce spurious diffs.
#
# https://docs.python.org/3/tutorial/modules.html#more-on-modules
epochMillis = 1000 * time.time()
useCurrentTimeInsteadOfEpochMillisForNoteStatusHistory = True
# Use this size threshld to isolate code which should be run differently in small
# scale unit tests.
minNumNotesForProdData = 200

# Explanation Tags
minRatingsToGetTag = 2
minTagsNeededForStatus = 2
tagPercentileForNormalization = 40
intervalHalfWidth = 0.3

# Max flip rates
prescoringAllUnlockedNotesMaxCrhChurn = 0.04
finalUnlockedNotesWithNoNewRatingsMaxCrhChurn = 0.03
finalNotesWithNewRatingsMaxCrhChurn = 0.40
finalNotesThatJustFlippedStatusMaxCrhChurn = 1e8
finalNotesThatFlippedRecentlyMaxCrhChurn = 1e8

# Data Filenames
scoredNotesOutputPath = "scoredNotes.tsv"
enrollmentInputPath = "userEnrollment-00000.tsv"
notesInputPath = "notes-00000.tsv"
ratingsInputPath = "ratings"
noteStatusHistoryInputPath = "noteStatusHistory-00000.tsv"

# TSV Column Names
participantIdKey = "participantId"
helpfulKey = "helpful"
notHelpfulKey = "notHelpful"
helpfulnessLevelKey = "helpfulnessLevel"
createdAtMillisKey = "createdAtMillis"
summaryKey = "summary"
noteTopicKey = "noteTopic"
authorTopNotHelpfulTagValues = "authorTopNotHelpfulTagValues"
modelingPopulationKey = "modelingPopulation"
modelingGroupKey = "modelingGroup"
numberOfTimesEarnedOutKey = "numberOfTimesEarnedOut"
defaultIndexKey = "index"

# Scoring Groups
coreGroups = {1, 2, 3, 6, 8, 9, 10, 11, 13, 14, 19, 21, 25}
expansionGroups = (
  # Divide into 3 grouping aggregates to prepare for multi-group models,
  # and a 4th group containing leftovers
  {0, 15, 17, 24, 29, 30} | {4, 5, 7, 12, 26} | {27} | {16, 20, 22, 23, 28}
)
expansionPlusGroups = {18}

# TSV Values
notHelpfulValueTsv = "NOT_HELPFUL"
somewhatHelpfulValueTsv = "SOMEWHAT_HELPFUL"
helpfulValueTsv = "HELPFUL"
notesSaysTweetIsMisleadingKey = "MISINFORMED_OR_POTENTIALLY_MISLEADING"
noteSaysTweetIsNotMisleadingKey = "NOT_MISLEADING"

# Fields Transformed From the Raw Data
helpfulNumKey = "helpfulNum"
ratingCreatedBeforeMostRecentNMRLabelKey = "ratingCreatedBeforeMostRecentNMRLabel"
ratingCreatedBeforePublicTSVReleasedKey = "ratingCreatedBeforePublicTSVReleased"

# Timestamps
deletedNoteTombstonesLaunchTime = 1652918400000  # May 19, 2022 UTC
notMisleadingUILaunchTime = 1664755200000  # October 3, 2022 UTC
lastRatingTagsChangeTimeMillis = 1639699200000  # 2021/12/15 UTC
publicTSVTimeDelay = 172800000  # 48 hours

# Explanation Tags
tagCountsKey = "tagCounts"
tiebreakOrderKey = "tiebreakOrder"
firstTagKey = "firstTag"
secondTagKey = "secondTag"
activeFilterTagsKey = "activeFilterTags"

# Contributor Counts
successfulRatingHelpfulCount = "successfulRatingHelpfulCount"
successfulRatingNotHelpfulCount = "successfulRatingNotHelpfulCount"
successfulRatingTotal = "successfulRatingTotal"
unsuccessfulRatingHelpfulCount = "unsuccessfulRatingHelpfulCount"
unsuccessfulRatingNotHelpfulCount = "unsuccessfulRatingNotHelpfulCount"
unsuccessfulRatingTotal = "unsuccessfulRatingTotal"
ratingsAwaitingMoreRatings = "ratingsAwaitingMoreRatings"
ratedAfterDecision = "ratedAfterDecision"
notesCurrentlyRatedHelpful = "notesCurrentlyRatedHelpful"
notesCurrentlyRatedNotHelpful = "notesCurrentlyRatedNotHelpful"
notesAwaitingMoreRatings = "notesAwaitingMoreRatings"

# Meta Scoring Columns
finalRatingStatusKey = "finalRatingStatus"
unlockedRatingStatusKey = "unlockedRatingStatus"
metaScorerActiveRulesKey = "metaScorerActiveRules"
decidedByKey = "decidedBy"
rescoringActiveRulesKey = "rescoringActiveRules"

# Note Status Changes Columns
noteFinalStatusChange = "finalStatusChange"
noteNewRatings = "newRatings"
noteDecidedByChange = "decidedByChange"
noteAllAddedRules = "allAddedRules"
noteAllRemovedRules = "allRemovedRules"
noteDecidedByInterceptChange = "decidedByInterceptChange"

# Internal Scoring Columns.  These columns should be renamed before writing to disk.
internalNoteInterceptKey = "internalNoteIntercept"
internalRaterInterceptKey = "internalRaterIntercept"
internalNoteFactorKeyBase = "internalNoteFactor"
internalRaterFactorKeyBase = "internalRaterFactor"
internalRatingStatusKey = "internalRatingStatus"
internalActiveRulesKey = "internalActiveRules"
internalRaterReputationKey = "internalRaterReputation"

scorerNameKey = "scorerName"


def note_factor_key(i):
  return internalNoteFactorKeyBase + str(i)


def rater_factor_key(i):
  return internalRaterFactorKeyBase + str(i)


internalNoteFactor1Key = note_factor_key(1)
internalRaterFactor1Key = rater_factor_key(1)

# Output Scoring Columns.
# Core Model
coreNoteInterceptKey = "coreNoteIntercept"
coreNoteFactor1Key = "coreNoteFactor1"
coreRaterInterceptKey = "coreRaterIntercept"
coreRaterFactor1Key = "coreRaterFactor1"
coreRatingStatusKey = "coreRatingStatus"
coreActiveRulesKey = "coreActiveRules"
coreNoteInterceptMaxKey = "coreNoteInterceptMax"
coreNoteInterceptMinKey = "coreNoteInterceptMin"
coreNumFinalRoundRatingsKey = "coreNumFinalRoundRatings"
# Expansion Model
expansionNoteInterceptKey = "expansionNoteIntercept"
expansionNoteFactor1Key = "expansionNoteFactor1"
expansionRatingStatusKey = "expansionRatingStatus"
expansionNoteInterceptMaxKey = "expansionNoteInterceptMax"
expansionNoteInterceptMinKey = "expansionNoteInterceptMin"
expansionInternalActiveRulesKey = "expansionActiveRules"
expansionNumFinalRoundRatingsKey = "expansionNumFinalRoundRatings"
expansionRaterFactor1Key = "expansionRaterFactor1"
expansionRaterInterceptKey = "expansionRaterIntercept"
# ExpansionPlus Model
expansionPlusNoteInterceptKey = "expansionPlusNoteIntercept"
expansionPlusNoteFactor1Key = "expansionPlusNoteFactor1"
expansionPlusRatingStatusKey = "expansionPlusRatingStatus"
expansionPlusInternalActiveRulesKey = "expansionPlusActiveRules"
expansionPlusNumFinalRoundRatingsKey = "expansionPlusNumFinalRoundRatings"
expansionPlusRaterFactor1Key = "expansionPlusRaterFactor1"
expansionPlusRaterInterceptKey = "expansionPlusRaterIntercept"
# Coverage / Helpfulness Reputation Model
coverageNoteInterceptKey = "coverageNoteIntercept"
coverageNoteFactor1Key = "coverageNoteFactor1"
coverageRatingStatusKey = "coverageRatingStatus"
coverageNoteInterceptMaxKey = "coverageNoteInterceptMax"
coverageNoteInterceptMinKey = "coverageNoteInterceptMin"
raterHelpfulnessReputationKey = "raterHelpfulnessReputation"
# Group Model
groupNoteInterceptKey = "groupNoteIntercept"
groupNoteFactor1Key = "groupNoteFactor1"
groupRatingStatusKey = "groupRatingStatus"
groupNoteInterceptMaxKey = "groupNoteInterceptMax"
groupNoteInterceptMinKey = "groupNoteInterceptMin"
groupRaterInterceptKey = "groupRaterIntercept"
groupRaterFactor1Key = "groupRaterFactor1"
groupInternalActiveRulesKey = "groupActiveRules"
groupNumFinalRoundRatingsKey = "groupNumFinalRoundRatings"
# Topic Model
topicNoteInterceptKey = "topicNoteIntercept"
topicNoteFactor1Key = "topicNoteFactor1"
topicRatingStatusKey = "topicRatingStatus"
topicNoteConfidentKey = "topicNoteConfident"
topicInternalActiveRulesKey = "topicActiveRules"
topicNumFinalRoundRatingsKey = "topicNumFinalRoundRatings"
# Harassment/Abuse Tag
harassmentNoteInterceptKey = "harassmentNoteIntercept"
harassmentNoteFactor1Key = "harassmentNoteFactor1"
harassmentRaterInterceptKey = "harassmentRaterIntercept"
harassmentRaterFactor1Key = "harassmentRaterFactor1"

# Ids and Indexes
noteIdKey = "noteId"
tweetIdKey = "tweetId"
classificationKey = "classification"
noteAuthorParticipantIdKey = "noteAuthorParticipantId"
raterParticipantIdKey = "raterParticipantId"

# Aggregations
noteCountKey = "noteCount"
ratingCountKey = "ratingCount"
numRatingsKey = "numRatings"
numRatingsLast28DaysKey = "numRatingsLast28"
ratingFromInitialModelingGroupKey = "ratingFromInitialModelingGroup"
percentFromInitialModelingGroupKey = "percentFromInitialModelingGroup"
numFinalRoundRatingsKey = "numFinalRoundRatings"

# Helpfulness Score Keys
crhRatioKey = "CRHRatio"
crnhRatioKey = "CRNHRatio"
crhCrnhRatioDifferenceKey = "crhCrnhRatioDifference"
meanNoteScoreKey = "meanNoteScore"
raterAgreeRatioKey = "raterAgreeRatio"
ratingAgreesWithNoteStatusKey = "ratingAgreesWithNoteStatus"
aboveHelpfulnessThresholdKey = "aboveHelpfulnessThreshold"
totalHelpfulHarassmentRatingsPenaltyKey = "totalHelpfulHarassmentPenalty"
raterAgreeRatioWithHarassmentAbusePenaltyKey = "raterAgreeRatioKeyWithHarassmentAbusePenalty"

# Note Status Labels
currentlyRatedHelpful = "CURRENTLY_RATED_HELPFUL"
currentlyRatedNotHelpful = "CURRENTLY_RATED_NOT_HELPFUL"
needsMoreRatings = "NEEDS_MORE_RATINGS"

# Boolean Note Status Labels
currentlyRatedHelpfulBoolKey = "crhBool"
currentlyRatedNotHelpfulBoolKey = "crnhBool"
awaitingMoreRatingsBoolKey = "awaitingBool"

helpfulOtherTagKey = "helpfulOther"

helpfulTagsAndTieBreakOrder = [
  (0, helpfulOtherTagKey),
  (8, "helpfulInformative"),
  (7, "helpfulClear"),
  (3, "helpfulEmpathetic"),
  (4, "helpfulGoodSources"),
  (2, "helpfulUniqueContext"),
  (5, "helpfulAddressesClaim"),
  (6, "helpfulImportantContext"),
  (1, "helpfulUnbiasedLanguage"),
]
helpfulTagsTSVOrder = [tag for (tiebreakOrder, tag) in helpfulTagsAndTieBreakOrder]
helpfulTagBoolsAndTypesTSVOrder = [(tag, pd.Int8Dtype()) for tag in helpfulTagsTSVOrder]
helpfulTagsTiebreakOrder = [tag for (tiebreakOrder, tag) in sorted(helpfulTagsAndTieBreakOrder)]
helpfulTagCountsAndTypesTSVOrder = [(tag, pd.Int64Dtype()) for tag in helpfulTagsTSVOrder]


# NOTE: Always add new tags to the end of this list, and *never* change the order of
# elements which are already in the list to maintain compatibility with
# BirdwatchNoteNotHelpfulTags.get in Scala.

notHelpfulIncorrectTagKey = "notHelpfulIncorrect"
notHelpfulOtherTagKey = "notHelpfulOther"
notHelpfulSpamHarassmentOrAbuseTagKey = "notHelpfulSpamHarassmentOrAbuse"
notHelpfulArgumentativeOrBiasedTagKey = "notHelpfulArgumentativeOrBiased"
notHelpfulHardToUnderstandKey = "notHelpfulHardToUnderstand"
notHelpfulNoteNotNeededKey = "notHelpfulNoteNotNeeded"
notHelpfulSourcesMissingOrUnreliableTagKey = "notHelpfulSourcesMissingOrUnreliable"
notHelpfulIrrelevantSourcesTagKey = "notHelpfulIrrelevantSources"
notHelpfulOpinionSpeculationOrBiasTagKey = "notHelpfulOpinionSpeculationOrBias"
notHelpfulMissingKeyPointsTagKey = "notHelpfulMissingKeyPoints"
notHelpfulOutdatedTagKey = "notHelpfulOutdated"
notHelpfulOffTopicTagKey = "notHelpfulOffTopic"
notHelpfulOpinionSpeculationTagKey = "notHelpfulOpinionSpeculation"

## This list is in TSV Order, but with indices for tiebreak order.
notHelpfulTagsAndTieBreakOrder = [
  (0, notHelpfulOtherTagKey),  ## should lose all tiebreaks
  (8, notHelpfulIncorrectTagKey),
  (2, notHelpfulSourcesMissingOrUnreliableTagKey),
  (4, notHelpfulOpinionSpeculationOrBiasTagKey),
  (5, notHelpfulMissingKeyPointsTagKey),
  (12, notHelpfulOutdatedTagKey),  ## should win all tiebreaks
  (10, notHelpfulHardToUnderstandKey),
  (7, notHelpfulArgumentativeOrBiasedTagKey),
  (9, notHelpfulOffTopicTagKey),
  (11, notHelpfulSpamHarassmentOrAbuseTagKey),
  (1, notHelpfulIrrelevantSourcesTagKey),
  (3, notHelpfulOpinionSpeculationTagKey),
  (6, notHelpfulNoteNotNeededKey),
]
notHelpfulTagsTSVOrder = [tag for (tiebreakOrder, tag) in notHelpfulTagsAndTieBreakOrder]
notHelpfulTagsAndTypesTSVOrder = [(tag, pd.Int8Dtype()) for tag in notHelpfulTagsTSVOrder]
notHelpfulTagCountsAndTypesTSVOrder = [(tag, pd.Int64Dtype()) for tag in notHelpfulTagsTSVOrder]
notHelpfulTagsTiebreakOrder = [
  tag for (tiebreakOrder, tag) in sorted(notHelpfulTagsAndTieBreakOrder)
]
notHelpfulTagsTiebreakMapping = {
  tag: priority for (priority, tag) in notHelpfulTagsAndTieBreakOrder
}
notHelpfulTagsEnumMapping = {
  tag: idx for (idx, (_, tag)) in enumerate(notHelpfulTagsAndTieBreakOrder)
}
adjustedSuffix = "Adjusted"
notHelpfulTagsAdjustedColumns = [f"{column}{adjustedSuffix}" for column in notHelpfulTagsTSVOrder]
notHelpfulTagsAdjustedTSVColumnsAndTypes = [
  (tag, np.double) for tag in notHelpfulTagsAdjustedColumns
]
ratioSuffix = "Ratio"
notHelpfulTagsAdjustedRatioColumns = [
  f"{column}{ratioSuffix}" for column in notHelpfulTagsAdjustedColumns
]
notHelpfulTagsAdjustedRatioTSVColumnsAndTypes = [
  (tag, np.double) for tag in notHelpfulTagsAdjustedRatioColumns
]
ratingWeightKey = "ratingWeight"

incorrectTagRatingsMadeByRaterKey = "incorrectTagRatingsMadeByRater"
totalRatingsMadeByRaterKey = "totalRatingsMadeByRater"

noteTfIdfIncorrectScoreKey = "tf_idf_incorrect"
numVotersKey = "num_voters"  # num voters who rated a note
incorrectTagRateByRaterKey = "p_incorrect_user"

noteTfIdfIncorrectScoreIntervalKey = (
  "tf_idf_incorrect_interval"  # note's tf-idf scores from within the interval
)
numVotersIntervalKey = "num_voters_interval"  # num voters (in the interval) who rated a note
sumOfIncorrectTagRateByRaterIntervalKey = (
  "p_incorrect_user_interval"
)  # sum of p_incorrect_user for all raters who rated a note in the interval
notHelpfulIncorrectIntervalKey = (
  "notHelpfulIncorrect_interval"  # notHelpfulIncorrect ratings on the note in the interval
)

lowDiligenceInterceptKey = "lowDiligenceIntercept"


lowDiligenceRaterFactor1Key = "lowDiligenceRaterFactor1"
lowDiligenceRaterInterceptKey = "lowDiligenceRaterIntercept"
lowDiligenceRaterReputationKey = "lowDiligenceRaterReputation"
lowDiligenceNoteFactor1Key = "lowDiligenceNoteFactor1"
lowDiligenceNoteInterceptKey = "lowDiligenceNoteIntercept"
lowDiligenceLegacyNoteInterceptKey = "lowDiligenceIntercept"
lowDiligenceNoteInterceptRound2Key = "lowDiligenceNoteInterceptRound2"
internalNoteInterceptRound2Key = "internalNoteInterceptRound2"
lowDiligenceRaterInterceptRound2Key = "lowDiligenceRaterInterceptRound2"
internalRaterInterceptRound2Key = "internalRaterInterceptRound2"

incorrectFilterColumnsAndTypes = [
  (notHelpfulIncorrectIntervalKey, np.double),
  (sumOfIncorrectTagRateByRaterIntervalKey, np.double),
  (numVotersIntervalKey, np.double),
  (noteTfIdfIncorrectScoreIntervalKey, np.double),
  (lowDiligenceLegacyNoteInterceptKey, np.double),
]
incorrectFilterColumns = [col for (col, _) in incorrectFilterColumnsAndTypes]

misleadingTags = [
  "misleadingOther",
  "misleadingFactualError",
  "misleadingManipulatedMedia",
  "misleadingOutdatedInformation",
  "misleadingMissingImportantContext",
  "misleadingUnverifiedClaimAsFact",
  "misleadingSatire",
]
misleadingTagsAndTypes = [(tag, pd.Int8Dtype()) for tag in misleadingTags]

notMisleadingTags = [
  "notMisleadingOther",
  "notMisleadingFactuallyCorrect",
  "notMisleadingOutdatedButNotWhenWritten",
  "notMisleadingClearlySatire",
  "notMisleadingPersonalOpinion",
]
notMisleadingTagsAndTypes = [(tag, pd.Int8Dtype()) for tag in notMisleadingTags]

noteTSVColumnsAndTypes = (
  [
    (noteIdKey, np.int64),
    (noteAuthorParticipantIdKey, object),
    (createdAtMillisKey, np.int64),
    (tweetIdKey, np.int64),
    (classificationKey, object),
    ("believable", "category"),
    ("harmful", "category"),
    ("validationDifficulty", "category"),
  ]
  + misleadingTagsAndTypes
  + notMisleadingTagsAndTypes
  + [("trustworthySources", pd.Int8Dtype()), (summaryKey, object), ("isMediaNote", pd.Int8Dtype())]
)
noteTSVColumns = [col for (col, dtype) in noteTSVColumnsAndTypes]
noteTSVTypes = [dtype for (col, dtype) in noteTSVColumnsAndTypes]
noteTSVTypeMapping = {col: dtype for (col, dtype) in noteTSVColumnsAndTypes}

versionKey = "version"
agreeKey = "agree"
disagreeKey = "disagree"
ratedOnTweetIdKey = "ratedOnTweetId"
ratingTSVColumnsAndTypes = (
  [
    (noteIdKey, np.int64),
    (raterParticipantIdKey, object),
    (createdAtMillisKey, np.int64),
    (versionKey, pd.Int8Dtype()),
    (agreeKey, pd.Int8Dtype()),
    (disagreeKey, pd.Int8Dtype()),
    (helpfulKey, pd.Int8Dtype()),
    (notHelpfulKey, pd.Int8Dtype()),
    (helpfulnessLevelKey, "category"),
  ]
  + helpfulTagBoolsAndTypesTSVOrder
  + notHelpfulTagsAndTypesTSVOrder
  + [(ratedOnTweetIdKey, np.int64)]
)

ratingTSVColumns = [col for (col, dtype) in ratingTSVColumnsAndTypes]
ratingTSVTypes = [dtype for (col, dtype) in ratingTSVColumnsAndTypes]
ratingTSVTypeMapping = {col: dtype for (col, dtype) in ratingTSVColumnsAndTypes}

timestampMillisOfNoteFirstNonNMRLabelKey = "timestampMillisOfFirstNonNMRStatus"
firstNonNMRLabelKey = "firstNonNMRStatus"
timestampMillisOfNoteCurrentLabelKey = "timestampMillisOfCurrentStatus"
currentLabelKey = "currentStatus"
timestampMillisOfNoteMostRecentNonNMRLabelKey = "timestampMillisOfLatestNonNMRStatus"
mostRecentNonNMRLabelKey = "mostRecentNonNMRStatus"
timestampMillisOfStatusLockKey = "timestampMillisOfStatusLock"
lockedStatusKey = "lockedStatus"
timestampMillisOfRetroLockKey = "timestampMillisOfRetroLock"
currentCoreStatusKey = "currentCoreStatus"
currentExpansionStatusKey = "currentExpansionStatus"
currentGroupStatusKey = "currentGroupStatus"
currentDecidedByKey = "currentDecidedBy"
currentModelingGroupKey = "currentModelingGroup"
timestampMillisOfMostRecentStatusChangeKey = "timestampMillisOfMostRecentStatusChange"

noteStatusHistoryTSVColumnsAndTypes = [
  (noteIdKey, np.int64),
  (noteAuthorParticipantIdKey, object),
  (createdAtMillisKey, np.int64),
  (timestampMillisOfNoteFirstNonNMRLabelKey, np.double),  # double because nullable.
  (firstNonNMRLabelKey, "category"),
  (timestampMillisOfNoteCurrentLabelKey, np.double),  # double because nullable.
  (currentLabelKey, "category"),
  (timestampMillisOfNoteMostRecentNonNMRLabelKey, np.double),  # double because nullable.
  (mostRecentNonNMRLabelKey, "category"),
  (timestampMillisOfStatusLockKey, np.double),  # double because nullable.
  (lockedStatusKey, "category"),
  (timestampMillisOfRetroLockKey, np.double),  # double because nullable.
  (currentCoreStatusKey, "category"),
  (currentExpansionStatusKey, "category"),
  (currentGroupStatusKey, "category"),
  (currentDecidedByKey, "category"),
  (currentModelingGroupKey, np.double),  # TODO: int
  (timestampMillisOfMostRecentStatusChangeKey, np.double),  # double because nullable.
]
noteStatusHistoryTSVColumns = [col for (col, dtype) in noteStatusHistoryTSVColumnsAndTypes]
noteStatusHistoryTSVTypes = [dtype for (col, dtype) in noteStatusHistoryTSVColumnsAndTypes]
noteStatusHistoryTSVTypeMapping = {
  col: dtype for (col, dtype) in noteStatusHistoryTSVColumnsAndTypes
}

# Earn In + Earn Out
enrollmentState = "enrollmentState"
successfulRatingNeededToEarnIn = "successfulRatingNeededToEarnIn"
timestampOfLastStateChange = "timestampOfLastStateChange"
timestampOfLastEarnOut = "timestampOfLastEarnOut"
authorTopNotHelpfulTagValues = "authorTopNotHelpfulTagValues"
maxHistoryEarnOut = 5
successfulRatingHelpfulCount = "successfulRatingHelpfulCount"
earnedIn = "earnedIn"
atRisk = "atRisk"
earnedOutNoAcknowledge = "earnedOutNoAcknowledge"
earnedOutAcknowledged = "earnedOutAcknowledged"
newUser = "newUser"
removed = "removed"
isAtRiskCRNHCount = 2
ratingImpactForEarnIn = 5
ratingImpact = "ratingImpact"
enrollmentStateToThrift = {
  earnedIn: 0,
  atRisk: 1,
  earnedOutNoAcknowledge: 2,
  earnedOutAcknowledged: 3,
  newUser: 4,
  removed: 5,
}
emergingWriterDays = 28
isEmergingWriterKey = "isEmergingWriter"
emergingMeanNoteScore = 0.3
emergingRatingCount = 10
aggregateRatingReceivedTotal = "aggregateRatingReceivedTotal"
core = "CORE"
expansion = "EXPANSION"
expansionPlus = "EXPANSION_PLUS"
topWriterWritingImpact = 10
topWriterHitRate = 0.04
hasCrnhSinceEarnOut = "hasCrnhSinceEarnOut"

userEnrollmentTSVColumnsAndTypes = [
  (participantIdKey, str),
  (enrollmentState, str),
  (successfulRatingNeededToEarnIn, np.int64),
  (timestampOfLastStateChange, np.int64),
  (timestampOfLastEarnOut, np.double),  # double because nullable.
  (modelingPopulationKey, str),
  (modelingGroupKey, np.float64),
  (numberOfTimesEarnedOutKey, np.int64),
]
userEnrollmentTSVColumns = [col for (col, _) in userEnrollmentTSVColumnsAndTypes]
userEnrollmentTSVTypes = [dtype for (_, dtype) in userEnrollmentTSVColumnsAndTypes]
userEnrollmentTSVTypeMapping = {col: dtype for (col, dtype) in userEnrollmentTSVColumnsAndTypes}

noteInterceptMaxKey = "internalNoteIntercept_max"
noteInterceptMinKey = "internalNoteIntercept_min"
noteParameterUncertaintyTSVMainColumnsAndTypes = [
  (noteInterceptMaxKey, np.double),
  (noteInterceptMinKey, np.double),
]
noteParameterUncertaintyTSVAuxColumnsAndTypes = [
  ("internalNoteFactor1_max", np.double),
  ("internalNoteFactor1_median", np.double),
  ("internalNoteFactor1_min", np.double),
  ("internalNoteFactor1_refit_orig", np.double),
  ("internalNoteIntercept_median", np.double),
  ("internalNoteIntercept_refit_orig", np.double),
  ("ratingCount_all", np.int64),
  ("ratingCount_neg_fac", np.int64),
  ("ratingCount_pos_fac", np.int64),
]
noteParameterUncertaintyTSVColumnsAndTypes = (
  noteParameterUncertaintyTSVAuxColumnsAndTypes + noteParameterUncertaintyTSVMainColumnsAndTypes
)
noteParameterUncertaintyTSVColumns = [
  col for (col, _) in noteParameterUncertaintyTSVColumnsAndTypes
]
noteParameterUncertaintyTSVAuxColumns = [
  col for (col, _) in noteParameterUncertaintyTSVAuxColumnsAndTypes
]
noteParameterUncertaintyTSVMainColumns = [
  col for (col, _) in noteParameterUncertaintyTSVMainColumnsAndTypes
]
noteParameterUncertaintyTSVTypes = [
  dtype for (_, dtype) in noteParameterUncertaintyTSVColumnsAndTypes
]
noteParameterUncertaintyTSVTypeMapping = {
  col: dtype for (col, dtype) in noteParameterUncertaintyTSVColumnsAndTypes
}

auxiliaryScoredNotesTSVColumnsAndTypes = (
  [
    (noteIdKey, np.int64),
    (ratingWeightKey, np.double),
    (createdAtMillisKey, np.int64),
    (noteAuthorParticipantIdKey, object),
    (awaitingMoreRatingsBoolKey, np.int8),
    (numRatingsLast28DaysKey, np.int64),
    (currentLabelKey, str),
    (currentlyRatedHelpfulBoolKey, np.int8),
    (currentlyRatedNotHelpfulBoolKey, np.int8),
    (unlockedRatingStatusKey, str),
  ]
  + helpfulTagCountsAndTypesTSVOrder
  + notHelpfulTagCountsAndTypesTSVOrder
  + notHelpfulTagsAdjustedTSVColumnsAndTypes
  + notHelpfulTagsAdjustedRatioTSVColumnsAndTypes
  + incorrectFilterColumnsAndTypes
)
auxiliaryScoredNotesTSVColumns = [col for (col, dtype) in auxiliaryScoredNotesTSVColumnsAndTypes]
auxiliaryScoredNotesTSVTypeMapping = {
  col: dtype for (col, dtype) in auxiliaryScoredNotesTSVColumnsAndTypes
}

deprecatedNoteModelOutputColumns = frozenset(
  {
    coverageNoteInterceptMinKey,
    coverageNoteInterceptMaxKey,
  }
)

prescoringNoteModelOutputTSVColumnsAndTypes = [
  (noteIdKey, np.int64),
  (internalNoteInterceptKey, np.double),
  (internalNoteFactor1Key, np.double),
  (scorerNameKey, str),
  (lowDiligenceNoteInterceptKey, np.double),
  (lowDiligenceNoteFactor1Key, np.double),
  (lowDiligenceNoteInterceptRound2Key, np.double),
]
prescoringNoteModelOutputTSVColumns = [
  col for (col, dtype) in prescoringNoteModelOutputTSVColumnsAndTypes
]
prescoringNoteModelOutputTSVTypeMapping = {
  col: dtype for (col, dtype) in prescoringNoteModelOutputTSVColumnsAndTypes
}

noteModelOutputTSVColumnsAndTypes = [
  (noteIdKey, np.int64),
  (coreNoteInterceptKey, np.double),
  (coreNoteFactor1Key, np.double),
  (finalRatingStatusKey, str),
  (firstTagKey, str),
  (secondTagKey, str),
  # Note that this column was formerly named "activeRules" and the name is now
  # updated to "coreActiveRules".  The data values remain the compatible,
  # but the new column only contains rules that ran when deciding status based on
  # the core model.
  (coreActiveRulesKey, str),
  (activeFilterTagsKey, str),
  (classificationKey, str),
  (createdAtMillisKey, np.int64),
  (coreRatingStatusKey, str),
  (metaScorerActiveRulesKey, str),
  (decidedByKey, str),
  (expansionNoteInterceptKey, np.double),
  (expansionNoteFactor1Key, np.double),
  (expansionRatingStatusKey, str),
  (coverageNoteInterceptKey, np.double),
  (coverageNoteFactor1Key, np.double),
  (coverageRatingStatusKey, str),
  (coreNoteInterceptMinKey, np.double),
  (coreNoteInterceptMaxKey, np.double),
  (expansionNoteInterceptMinKey, np.double),
  (expansionNoteInterceptMaxKey, np.double),
  (coverageNoteInterceptMinKey, np.double),
  (coverageNoteInterceptMaxKey, np.double),
  (groupNoteInterceptKey, np.double),
  (groupNoteFactor1Key, np.double),
  (groupRatingStatusKey, str),
  (groupNoteInterceptMaxKey, np.double),
  (groupNoteInterceptMinKey, np.double),
  (modelingGroupKey, np.float64),
  (numRatingsKey, np.int64),
  (timestampMillisOfNoteCurrentLabelKey, np.double),
  (expansionPlusNoteInterceptKey, np.double),
  (expansionPlusNoteFactor1Key, np.double),
  (expansionPlusRatingStatusKey, str),
  (topicNoteInterceptKey, np.double),
  (topicNoteFactor1Key, np.double),
  (topicRatingStatusKey, str),
  (noteTopicKey, str),
  (topicNoteConfidentKey, pd.BooleanDtype()),
  (expansionInternalActiveRulesKey, str),
  (expansionPlusInternalActiveRulesKey, str),
  (groupInternalActiveRulesKey, str),
  (topicInternalActiveRulesKey, str),
  (coreNumFinalRoundRatingsKey, np.double),  # double because nullable.
  (expansionNumFinalRoundRatingsKey, np.double),  # double because nullable.
  (expansionPlusNumFinalRoundRatingsKey, np.double),  # double because nullable.
  (groupNumFinalRoundRatingsKey, np.double),  # double because nullable.
  (topicNumFinalRoundRatingsKey, np.double),  # double because nullable.
  (rescoringActiveRulesKey, str),
]
noteModelOutputTSVColumns = [col for (col, dtype) in noteModelOutputTSVColumnsAndTypes]
noteModelOutputTSVTypeMapping = {col: dtype for (col, dtype) in noteModelOutputTSVColumnsAndTypes}
deprecatedNoteModelOutputTSVColumnsAndTypes = [
  (col, dtype)
  for (col, dtype) in noteModelOutputTSVColumnsAndTypes
  if col in deprecatedNoteModelOutputColumns
]

postSelectionValueKey = "postSelectionValue"

prescoringRaterModelOutputTSVColumnsAndTypes = [
  (raterParticipantIdKey, object),
  (internalRaterInterceptKey, np.double),
  (internalRaterFactor1Key, np.double),
  (crhCrnhRatioDifferenceKey, np.double),
  (meanNoteScoreKey, np.double),
  (raterAgreeRatioKey, np.double),
  (aboveHelpfulnessThresholdKey, pd.BooleanDtype()),
  (scorerNameKey, str),
  (internalRaterReputationKey, np.double),
  (lowDiligenceRaterInterceptKey, np.double),
  (lowDiligenceRaterFactor1Key, np.double),
  (lowDiligenceRaterReputationKey, np.double),
  (lowDiligenceRaterInterceptRound2Key, np.double),
  (incorrectTagRatingsMadeByRaterKey, pd.Int64Dtype()),
  (totalRatingsMadeByRaterKey, pd.Int64Dtype()),
  (postSelectionValueKey, pd.Int64Dtype()),
]
prescoringRaterModelOutputTSVColumns = [
  col for (col, dtype) in prescoringRaterModelOutputTSVColumnsAndTypes
]
prescoringRaterModelOutputTSVTypeMapping = {
  col: dtype for (col, dtype) in prescoringRaterModelOutputTSVColumnsAndTypes
}

raterModelOutputTSVColumnsAndTypes = [
  (raterParticipantIdKey, np.int64),
  (coreRaterInterceptKey, np.double),
  (coreRaterFactor1Key, np.double),
  (crhCrnhRatioDifferenceKey, np.double),
  (meanNoteScoreKey, np.double),
  (raterAgreeRatioKey, np.double),
  (successfulRatingHelpfulCount, pd.Int64Dtype()),
  (successfulRatingNotHelpfulCount, pd.Int64Dtype()),
  (successfulRatingTotal, pd.Int64Dtype()),
  (unsuccessfulRatingHelpfulCount, pd.Int64Dtype()),
  (unsuccessfulRatingNotHelpfulCount, pd.Int64Dtype()),
  (unsuccessfulRatingTotal, pd.Int64Dtype()),
  (ratingsAwaitingMoreRatings, pd.Int64Dtype()),
  (ratedAfterDecision, pd.Int64Dtype()),
  (notesCurrentlyRatedHelpful, pd.Int64Dtype()),
  (notesCurrentlyRatedNotHelpful, pd.Int64Dtype()),
  (notesAwaitingMoreRatings, pd.Int64Dtype()),
  (enrollmentState, pd.Int64Dtype()),
  (successfulRatingNeededToEarnIn, pd.Int64Dtype()),
  (authorTopNotHelpfulTagValues, str),
  (timestampOfLastStateChange, np.double),
  (aboveHelpfulnessThresholdKey, np.float64),  # nullable bool.
  (isEmergingWriterKey, pd.BooleanDtype()),
  (aggregateRatingReceivedTotal, pd.Int64Dtype()),
  (timestampOfLastEarnOut, np.double),
  (groupRaterInterceptKey, np.double),
  (groupRaterFactor1Key, np.double),
  (modelingGroupKey, np.float64),
  (raterHelpfulnessReputationKey, np.double),
  (numberOfTimesEarnedOutKey, np.float64),
  (expansionRaterInterceptKey, np.double),
  (expansionRaterFactor1Key, np.double),
  (expansionPlusRaterInterceptKey, np.double),
  (expansionPlusRaterFactor1Key, np.double),
]
raterModelOutputTSVColumns = [col for (col, dtype) in raterModelOutputTSVColumnsAndTypes]
raterModelOutputTSVTypeMapping = {col: dtype for (col, dtype) in raterModelOutputTSVColumnsAndTypes}

noteStatusChangesPrev = "_prev"
noteStatusChangesDerivedColumnsAndTypes = [
  (noteIdKey, np.int64),
  (noteFinalStatusChange, str),
  (noteNewRatings, np.int64),
  (noteDecidedByChange, str),
  (noteAllAddedRules, str),
  (noteAllRemovedRules, str),
  (noteDecidedByInterceptChange, str),
]
noteStatusChangesRemovedCols = [
  col
  for col in noteModelOutputTSVColumns
  if ("NoteInterceptMin" in col) or ("NoteInterceptMax" in col)
]
noteStatusChangesModelOutputColumnsAndTypes = [
  (col, t)
  for (col, t) in noteModelOutputTSVColumnsAndTypes
  if col not in noteStatusChangesRemovedCols + [noteIdKey]
]
noteStatusChangesModelOutputWithPreviousColumnsAndTypes = (
  noteStatusChangesModelOutputColumnsAndTypes
  + [(col + noteStatusChangesPrev, t) for (col, t) in noteStatusChangesModelOutputColumnsAndTypes]
)

noteStatusChangeTSVColumnsAndTypes = noteStatusChangesDerivedColumnsAndTypes + sorted(
  noteStatusChangesModelOutputWithPreviousColumnsAndTypes, key=lambda tup: tup[0]
)
noteStatusChangesTSVColumns = [col for (col, dtype) in noteStatusChangeTSVColumnsAndTypes]
noteStatusChangesTSVTypeMapping = {
  col: dtype for (col, dtype) in noteStatusChangeTSVColumnsAndTypes
}

datasetKeyKey = "datasetKey"
partitionToReadKey = "partitionToRead"
fileNameToReadKey = "fileNameToRead"
inputPathsTSVColumnsAndTypes = [
  (datasetKeyKey, str),
  (partitionToReadKey, str),
  (fileNameToReadKey, str),
]
inputPathsTSVColumns = [col for (col, _) in inputPathsTSVColumnsAndTypes]
inputPathsTSVTypeMapping = {col: dtype for (col, dtype) in inputPathsTSVColumnsAndTypes}


@contextmanager
def time_block(label):
  start = time.time()
  try:
    yield
  finally:
    end = time.time()
    print(f"{label} elapsed time: {end - start:.2f} secs ({((end - start) / 60.0):.2f} mins)")


### TODO: weave through second round intercept.
@dataclass
class ReputationGlobalIntercept:
  firstRound: float
  secondRound: float
  finalRound: float


@dataclass
class PrescoringMetaScorerOutput:
  globalIntercept: Optional[float]
  lowDiligenceGlobalIntercept: Optional[ReputationGlobalIntercept]
  tagFilteringThresholds: Optional[Dict[str, float]]  # tag => threshold


@dataclass
class PrescoringMetaOutput:
  metaScorerOutput: Dict[str, PrescoringMetaScorerOutput]  # scorerName => output


@dataclass
class SharedMemoryDataframeInfo:
  sharedMemoryName: str
  dataSize: int


@dataclass
class ScoringArgsSharedMemory:
  noteTopics: SharedMemoryDataframeInfo
  ratings: SharedMemoryDataframeInfo
  noteStatusHistory: SharedMemoryDataframeInfo
  userEnrollment: SharedMemoryDataframeInfo


@dataclass
class PrescoringArgsSharedMemory(ScoringArgsSharedMemory):
  pass


@dataclass
class FinalScoringArgsSharedMemory(ScoringArgsSharedMemory):
  prescoringNoteModelOutput: SharedMemoryDataframeInfo
  prescoringRaterModelOutput: SharedMemoryDataframeInfo


@dataclass
class ScoringArgs:
  noteTopics: pd.DataFrame
  ratings: pd.DataFrame
  noteStatusHistory: pd.DataFrame
  userEnrollment: pd.DataFrame

  def remove_large_args_for_multiprocessing(self):
    self.noteTopics = None
    self.ratings = None
    self.noteStatusHistory = None
    self.userEnrollment = None


@dataclass
class PrescoringArgs(ScoringArgs):
  pass


@dataclass
class FinalScoringArgs(ScoringArgs):
  prescoringNoteModelOutput: pd.DataFrame
  prescoringRaterModelOutput: pd.DataFrame
  prescoringMetaOutput: PrescoringMetaOutput

  def remove_large_args_for_multiprocessing(self):
    self.ratings = None
    self.noteStatusHistory = None
    self.userEnrollment = None
    self.prescoringNoteModelOutput = None
    self.prescoringRaterModelOutput = None


@dataclass
class ModelResult:
  scoredNotes: pd.DataFrame
  helpfulnessScores: pd.DataFrame
  auxiliaryNoteInfo: pd.DataFrame
  scorerName: Optional[str]
  metaScores: Optional[PrescoringMetaScorerOutput]


class RescoringRuleID(Enum):
  ALL_NOTES = 1
  NOTES_WITH_NEW_RATINGS = 2
  NOTES_FLIPPED_PREVIOUS_RUN = 3
  NEW_NOTES_NOT_RESCORED_RECENTLY_ENOUGH = 4
  RECENTLY_FLIPPED_NOTES_NOT_RESCORED_RECENTLY_ENOUGH = 5


@dataclass
class NoteSubset:
  noteSet: Optional[set]
  maxCrhChurnRate: float
  description: RescoringRuleID
