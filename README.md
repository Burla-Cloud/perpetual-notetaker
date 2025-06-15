

### Perpetual Notetaker 

An always-on 24/7 notaker listening to and summarizing all conversations that happen in my living room.

#### Goal: Whenever my co-founders and I have a conversation, an AI meeting summary automatically appears in Slack.

### Motivation:

My name is Jake, I'm a co-founder of [Burla.dev](https://Burla.dev).  
My two co-founders and I live in the same apartment in Boston, and frequently have conversations about our startup in our living room.  

We're pretty good at talking for two hours, writing nothing down, then forgetting what we talked about.  
To prevent this we started using the [Otter.ai](https://Otter.ai) app on our phones to record and summarize these conversations.  
The problem is:
- Sometimes we forget to take out our phone and hit record.
- Sometimes we talk for a really long time, and Otter only records for up to 30 minutes at once (on the free plan).
- We have frequent conversations, and Otter only transcribes 300 minutes a month (also on the free plan).

Most normal people would just buy the $30/month business plan (up to 4hr meetings, 6000 min/month).  
But that wouldn't solve our problem of not remembering to hit record, also it's more fun to build our own!


### Components:

#### `/listener`:
The "listener" is a Rasberry Pi with a mic, on 24/7 in my living room.

#### `/notetaker`:
The "notetaker" is a backend webservice that the listener sends audio to.  
This service identifies conversations, creates AI summaries, and posts them in Slack.