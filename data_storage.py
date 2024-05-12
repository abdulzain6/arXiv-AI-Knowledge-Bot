import contextlib
from peewee import *



class PDFFileManager:
    def __init__(self, db: SqliteDatabase):
        class PDFFile(Model):
            namespace = CharField()
            pdf_name = CharField(unique=True)
            pdf_title = CharField()

            class Meta:
                database = db
                
        self.model = PDFFile
        db.connect(reuse_if_open=True)
        db.create_tables([PDFFile], safe=True)

    def create_pdf_file(self, namespace: str, pdf_name: str, pdf_title: str):
        with contextlib.suppress(Exception):
            pdf_file = self.model(namespace=namespace, pdf_name=pdf_name, pdf_title=pdf_title)
            pdf_file.save(force_insert=True)

    def read_pdf_file(self, pdf_name: str):
        try:
            return self.model.get(self.model.pdf_name == pdf_name)
        except DoesNotExist:
            return None

    def update_pdf_file(self, pdf_name: str, pdf_title: str):
        pdf_file = self.model.get(self.model.pdf_name == pdf_name)
        pdf_file.pdf_title = pdf_title
        pdf_file.save()

    def delete_pdf_file(self, pdf_name: str):
        pdf_file = self.model.get(self.model.pdf_name == pdf_name)
        pdf_file.delete_instance()
        
    def get_all_pdfs(self) -> list:
        return list(self.model.select())

    def get_pdf_by_name(self, pdf_name: str):
        try:
            return self.model.get(self.model.pdf_name == pdf_name)
        except DoesNotExist:
            return None
    

class ChatManager:
    def __init__(self, db: SqliteDatabase) -> None:
        
        class ChatMessage(Model):
            ai_message = TextField()
            human_message = TextField()
            sequence_number = IntegerField()
            namespace = CharField()

            class Meta:
                database = db
                
        self.model = ChatMessage
        db.connect(reuse_if_open=True)
        db.create_tables([ChatMessage], safe=True)
        
    def add_message(self, namespace: str, ai_message: str, human_message: str) -> None:
        last_message = self.model.select().where(self.model.namespace == namespace).order_by(
            self.model.sequence_number.desc()).first()

        if last_message is None:
            sequence_number = 0
        else:
            sequence_number = last_message.sequence_number + 1

        self.model.create(namespace=namespace, ai_message=ai_message, human_message=human_message,
                            sequence_number=sequence_number)

    def retrieve_all_messages(self, namespace: str):
        query = self.model.select().where(self.model.namespace == namespace).order_by(self.model.sequence_number)
        return [(row.human_message, row.ai_message) for row in query]
    