# Data Dictionary

This document lists the database tables and their fields.

## Study
- **id** (`Integer`): Primary key.
- **title** (`String`): Study title.
- **year** (`Integer`): Publication year.
- **journal** (`String`): Journal name.
- **doi** (`String`, unique): Digital Object Identifier.
- **authors_text** (`Text`): Authors as provided in source.
- **country** (`String`): Country of origin.
- **design** (`String`): Study design.
- **notes** (`Text`): Additional notes.
- **created_at** (`DateTime`): Creation timestamp.
- **updated_at** (`DateTime`): Last modification timestamp.

## Arm
- **id** (`Integer`): Primary key.
- **study_id** (`Integer`, FK): Related study.
- **name** (`String`): Arm label.
- **n** (`Integer`): Sample size.
- **desc** (`Text`): Description.

## Outcome
- **id** (`Integer`): Primary key.
- **study_id** (`Integer`, FK): Related study.
- **name** (`String`): Outcome name.
- **unit** (`String`): Measurement unit.
- **direction** (`String`): Direction of effect.
- **domain** (`String`): Outcome domain.
- **method** (`String`): Measurement technique.

## Effect
- **id** (`Integer`): Primary key.
- **study_id** (`Integer`, FK): Related study.
- **outcome_id** (`Integer`, FK): Related outcome.
- **arm_id** (`Integer`, FK, nullable): Arm-specific effect.
- **arm_treat_id** (`Integer`, FK, nullable): Treatment arm for comparative effect.
- **arm_ctrl_id** (`Integer`, FK, nullable): Control arm for comparative effect.
- **effect_type** (`Enum`): SMD, MD, logOR or RR.
- **effect** (`Float`): Effect size.
- **se** (`Float`): Standard error.
- **ci_low** (`Float`): Lower confidence interval.
- **ci_high** (`Float`): Upper confidence interval.
- **mean** (`Float`): Mean value.
- **sd** (`Float`): Standard deviation.
- **n** (`Integer`): Sample size.
- **events** (`Integer`): Number of events.
- **total** (`Integer`): Total participants.

## Covariate
- **id** (`Integer`): Primary key.
- **study_id** (`Integer`, FK): Related study.
- **name** (`String`): Covariate name.
- **value** (`String`): Covariate value.

## Tag
- **id** (`Integer`): Primary key.
- **name** (`String`, unique): Tag name.

## StudyTag
- **study_id** (`Integer`, FK): Study reference.
- **tag_id** (`Integer`, FK): Tag reference.

## User
- **id** (`Integer`): Primary key.
- **email** (`String`, unique): Email address.
- **password_hash** (`String`): Password hash.
- **role** (`String`): User role.

