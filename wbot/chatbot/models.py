from django.db import models

class Topic(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Question(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    question_text = models.TextField()
    answer_yes = models.TextField()
    answer_no = models.TextField()

    def __str__(self):
        return self.question_text

class UserSession(models.Model):
    phone_number = models.CharField(max_length=20, unique=True)
    current_topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    question_index = models.IntegerField(default=0)
    answered_questions = models.ManyToManyField(Question, blank=True)
    
    #Add this for paginated button, I'll comment it for a while, nitatumia kama approach ya pili.
    # topic_page = models.IntegerField(default=1)

