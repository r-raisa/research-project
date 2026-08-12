# Data audit

This file records the datasets downloaded and inspected for the project.


## counsel_chat

- Local path: `/Users/raisa/Desktop/Research Project/git-repo/research-project/data/raw/counsel_chat`

- Splits: ['train']


### Split: train

- Rows: 2775

- Columns: `['questionID', 'questionTitle', 'questionText', 'questionLink', 'topic', 'therapistInfo', 'therapistURL', 'answerText', 'upvotes', 'views']`


#### Example 0

- `questionID`: 0

- `questionTitle`: Do I have too many issues for counseling?

- `questionText`: I have so many issues to address. I have a history of sexual abuse, I’m a breast cancer survivor and I am a lifetime insomniac.    I have a long history of depression and I’m beginning to have anxiety. I have low self esteem but I’ve been happily married for almost 35 years.
   I’ve never had counseling about any of this. Do I have too many issues to address in counseling?

- `questionLink`: https://counselchat.com/questions/do-i-have-too-many-issues-for-counseling

- `topic`: depression

- `therapistInfo`: Jennifer MolinariHypnotherapist & Licensed Counselor

- `therapistURL`: https://counselchat.com/therapists/jennifer-molinari

- `answerText`: It is very common for people to have multiple issues that they want to (and need to) address in counseling.  I have had clients ask that same question and through more exploration, there is often an underlying fear that they  "can't be helped" or that they will "be too much for their therapist." I don't know if any of this rings true for you. But, most people have more than one problem in their lives and more often than not,  people have numerous significant stressors in their lives.  Let's face...

- `upvotes`: 3

- `views`: 1971


#### Example 1

- `questionID`: 0

- `questionTitle`: Do I have too many issues for counseling?

- `questionText`: I have so many issues to address. I have a history of sexual abuse, I’m a breast cancer survivor and I am a lifetime insomniac.    I have a long history of depression and I’m beginning to have anxiety. I have low self esteem but I’ve been happily married for almost 35 years.
   I’ve never had counseling about any of this. Do I have too many issues to address in counseling?

- `questionLink`: https://counselchat.com/questions/do-i-have-too-many-issues-for-counseling

- `topic`: depression

- `therapistInfo`: Jason Lynch, MS, LMHC, LCAC, ADSIndividual & Couples Therapy

- `therapistURL`: https://counselchat.com/therapists/jason-lynch-ms-lmhc-lcac-ads

- `answerText`: I've never heard of someone having "too many issues" for therapy to be effective. A competent therapist will assist you in identifying the root causes of your problems and treat those first. If the underlying issues are addressed, your various symptoms should improve. For example, a history of sexual trauma can cause sleep disturbances, depression, anxiety, and low self-worth. I would start by addressing the underlying trauma using EMDR Therapy. EMDR allows the client to process unresolved traum...

- `upvotes`: 2

- `views`: 386


### Dataset Observations

- Useful fields: questionTitle, questionText, topic, answerText, upvotes.
- Primary use: use questionText as therapy style user prompts because it contains natural mental-health related questions.
- Secondary use: use answerText only as a candidate reference response for supervised fine-tuning after quality filtering. These answers will not be treated automatically as perfect responses. Use upvotes as a quality signal for filtering candidate responses.
- Excluded fields: questionLink, therapistInfo, and therapistURL will not be used for modelling because they are not needed and may introduce unnecessary identifying metadata.
- Data Cleaning: Contains duplicate questions, these will either be removed (using questionID) or normalised (using questionText). The prompts should only appear once in prompt pool.
- Limitations: This dataset is a counselling Q&A format, not an interactive therapy dialogue. Some answers may include clinical advice, diagnosis wording or specific treatment recommendations, responses must be checked before being used for training.
- Use in project: main source of mental-health-style prompts; possible source of candidate safe responses after filtering.


## empathetic_dialogues

- Local path: `/Users/raisa/Desktop/Research Project/git-repo/research-project/data/raw/empathetic_dialogues`

- Splits: ['train', 'validation', 'test']


### Split: train

- Rows: 76673

- Columns: `['conv_id', 'utterance_idx', 'context', 'prompt', 'speaker_idx', 'utterance', 'selfeval', 'tags']`


#### Example 0

- `conv_id`: hit:0_conv:1

- `utterance_idx`: 1

- `context`: sentimental

- `prompt`: I remember going to the fireworks with my best friend. There was a lot of people_comma_ but it only felt like us in the world.

- `speaker_idx`: 1

- `utterance`: I remember going to see the fireworks with my best friend. It was the first time we ever spent time alone together. Although there was a lot of people_comma_ we felt like the only people in the world.

- `selfeval`: 5|5|5_2|2|5

- `tags`: 


#### Example 1

- `conv_id`: hit:0_conv:1

- `utterance_idx`: 2

- `context`: sentimental

- `prompt`: I remember going to the fireworks with my best friend. There was a lot of people_comma_ but it only felt like us in the world.

- `speaker_idx`: 0

- `utterance`: Was this a friend you were in love with_comma_ or just a best friend?

- `selfeval`: 5|5|5_2|2|5

- `tags`: 


### Split: validation

- Rows: 12030

- Columns: `['conv_id', 'utterance_idx', 'context', 'prompt', 'speaker_idx', 'utterance', 'selfeval', 'tags']`


#### Example 0

- `conv_id`: hit:3_conv:6

- `utterance_idx`: 1

- `context`: terrified

- `prompt`: Today_comma_as i was leaving for work in the morning_comma_i had a tire burst in the middle of a busy road. That scared the hell out of me!

- `speaker_idx`: 6

- `utterance`: Today_comma_as i was leaving for work in the morning_comma_i had a tire burst in the middle of a busy road. That scared the hell out of me!

- `selfeval`: 4|5|5_5|5|5

- `tags`: 


#### Example 1

- `conv_id`: hit:3_conv:6

- `utterance_idx`: 2

- `context`: terrified

- `prompt`: Today_comma_as i was leaving for work in the morning_comma_i had a tire burst in the middle of a busy road. That scared the hell out of me!

- `speaker_idx`: 7

- `utterance`: Are you fine now?

- `selfeval`: 4|5|5_5|5|5

- `tags`: 


### Split: test

- Rows: 10943

- Columns: `['conv_id', 'utterance_idx', 'context', 'prompt', 'speaker_idx', 'utterance', 'selfeval', 'tags']`


#### Example 0

- `conv_id`: hit:0_conv:0

- `utterance_idx`: 1

- `context`: guilty

- `prompt`: I felt guilty when I was driving home one night and a person tried to fly into my lane_comma_ and didn't see me. I honked and they swerved back into their lane_comma_ slammed on their brakes_comma_ and hit the water cones.

- `speaker_idx`: 0

- `utterance`: Yeah about 10 years ago I had a horrifying experience. It was 100% their fault but they hit the water barrels and survived. They had no injuries but they almost ran me off the road.

- `selfeval`: 2|2|5_5|5|5

- `tags`: 


#### Example 1

- `conv_id`: hit:0_conv:0

- `utterance_idx`: 2

- `context`: guilty

- `prompt`: I felt guilty when I was driving home one night and a person tried to fly into my lane_comma_ and didn't see me. I honked and they swerved back into their lane_comma_ slammed on their brakes_comma_ and hit the water cones.

- `speaker_idx`: 1

- `utterance`: Did you suffer any injuries?

- `selfeval`: 2|2|5_5|5|5

- `tags`: 


### Dataset Observations

- Useful fields: context, prompt, utterance, conv_id, utterance_idx, and speaker_idx.
- Primary use: use this dataset only as a source of general empathy-style language and low-risk emotional support examples.
- Secondary use: use context as an emotion label and prompt as an emotional situation where relevant.
- Excluded use: this dataset will not be treated as therapy specific or clinically safe data because many examples are everyday emotional situations rather than mental health support conversations.
- Data Cleaning: replace dataset artefacts such as _comma_ with normal punctuation. Deduplicate repeated prompts by conv_id and prompt.
- Limitations: the dataset is useful for empathy, but it does not directly teach crisis escalation, therapeutic boundaries, or mental health safety. It should therefore not dominate the training or evaluation data.
- Use in project: : optional supplementary source for empathy-style examples
- Notes: this is the largest dataset - needs to be sampled or could push the model toward general empathy at the expense of clinical safety.


## esconv

- Local path: `/Users/raisa/Desktop/Research Project/git-repo/research-project/data/raw/esconv`

- Splits: ['train', 'validation', 'test']


### Split: train

- Rows: 910

- Columns: `['text']`


#### Example 0

- `text`: {"experience_type": "Current Experience", "emotion_type": "anxiety", "problem_type": "job crisis", "situation": "I am on short term disability and I am afraid I will lose my job if I don't go back soon.", "survey_score": {"seeker": {"initial_emotion_intensity": "3", "empathy": "5", "relevance": "5", "final_emotion_intensity": "2"}, "supporter": {"relevance": "5"}}, "dialog": [{"text": "Hello good afternoon.", "speaker": "usr"}, {"text": "Hi, good afternoon.", "speaker": "sys", "strategy": "Quest...


#### Example 1

- `text`: {"experience_type": "Current Experience", "emotion_type": "depression", "problem_type": "ongoing depression", "situation": "I have been in a depression since my father died last year. We have had to sell our home and move to a much smaller place due to losing his income. I am older but lived with my parents to help them because they are both ill. it has been an ongoing struggle", "survey_score": {"seeker": {"initial_emotion_intensity": "4", "empathy": "4", "relevance": "5", "final_emotion_intens...


### Split: validation

- Rows: 195

- Columns: `['text']`


#### Example 0

- `text`: {"experience_type": "Previous Experience", "emotion_type": "depression", "problem_type": "academic pressure", "situation": "I used to love my field of study, But soon after entering the university I started skipping the classes and failing. I lost my interest and there was nothing to motivate me.", "survey_score": {"seeker": {"initial_emotion_intensity": "4", "empathy": "4", "relevance": "4", "final_emotion_intensity": "2"}, "supporter": {}}, "dialog": [{"text": "Hi, what I can help you with tod...


#### Example 1

- `text`: {"experience_type": "Current Experience", "emotion_type": "anger", "problem_type": "job crisis", "situation": "I have a co worker that keeps going behind my back and trying to get things done without me knowing it.", "survey_score": {"seeker": {"initial_emotion_intensity": "3", "empathy": "2", "relevance": "5", "final_emotion_intensity": "2"}, "supporter": {"relevance": "5"}}, "dialog": [{"text": "Hi, how are you?", "speaker": "sys", "strategy": "Others"}, {"text": "I'm ok just kind of sick of t...


### Split: test

- Rows: 195

- Columns: `['text']`


#### Example 0

- `text`: {"experience_type": "Current Experience", "emotion_type": "depression", "problem_type": "ongoing depression", "situation": "I am always depressed and the upcoming holidays are making it a lot worse.", "survey_score": {"seeker": {"initial_emotion_intensity": "4", "empathy": "5", "relevance": "5", "final_emotion_intensity": "3"}, "supporter": {"relevance": "5"}}, "dialog": [{"text": "Hello. How are you today?", "speaker": "sys", "strategy": "Others"}, {"text": "hi i am okay, a little bit sad thoug...


#### Example 1

- `text`: {"experience_type": "Current Experience", "emotion_type": "sadness", "problem_type": "job crisis", "situation": "I have been put into sadness due to pressure from my employer who is threatening to down size the manpower at work. I am really sad because my supervisor has mentioned to me that I am going to be one of those who are going to lose their jobs.", "survey_score": {"seeker": {"initial_emotion_intensity": "5", "empathy": "4", "relevance": "4", "final_emotion_intensity": "3"}, "supporter": ...


### Dataset Observations

- To be confirmed after manual inspection.
