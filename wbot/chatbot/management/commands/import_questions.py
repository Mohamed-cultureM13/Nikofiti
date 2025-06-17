import json
import os
from django.core.management.base import BaseCommand
from chatbot.models import Topic, Question

# Bash command: python manage.py import_questions
# This command imports questions and topics from a JSON file into the database.


class Command(BaseCommand):
    help = 'Import questions and topics from a JSON file'

    def handle(self, *args, **kwargs):
        # file_path = os.path.join('chatbot', 'question_data.json')
        # file_path = os.path.join('chatbot', 'nikofiti.json')
        file_path = os.path.join('chatbot', 'new_questions.json')
        if not os.path.exists(file_path):   
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for topic_data in data:
            topic_name = topic_data["topic"]
            topic, _ = Topic.objects.get_or_create(name=topic_name)

            for q in topic_data["questions"]:
                Question.objects.get_or_create(
                    topic=topic,
                    question_text=q["question"],
                    answer_yes=q["answer_yes"],
                    answer_no=q["answer_no"]
                )

        self.stdout.write(self.style.SUCCESS("✅ Questions imported successfully!"))
