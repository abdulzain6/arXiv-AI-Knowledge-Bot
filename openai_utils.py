from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.llms import OpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import CharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from data_storage import ChatManager
from langchain.chains import LLMChain
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains.question_answering import load_qa_chain
from langchain.chains.conversational_retrieval.prompts import CONDENSE_QUESTION_PROMPT
from globals import creds, config
import hashlib

def summarize_pdf(docs) -> str:
    llm = ChatOpenAI(
        temperature=0,
        openai_api_key=creds["OPENAI_API_KEY"],
        model_name=config["MODEL_NAME"],
    )
    chain = load_summarize_chain(llm, chain_type="map_reduce", verbose=True)
    return chain.run(docs)


def generate_unique_string(input_string: str, length: int) -> str:
    hashed_string = hashlib.sha256(input_string.encode()).hexdigest()
    return hashed_string[:length]


def add_pdf_to_memory(filepath: str) -> str:
    loader = PyPDFLoader(filepath)
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000, chunk_overlap=0
    )
    pages = loader.load_and_split(text_splitter=text_splitter)
    namespace = f"{generate_unique_string(filepath, 7)}__{filepath}"
    Pinecone.from_documents(
        pages,
        HuggingFaceEmbeddings(),
        index_name=creds["INDEX_NAME"],
        namespace=namespace,
    )
    return namespace, pages




class ChatRetrievalWithDB:
    def __init__(self, namespace: str, index_name: str, embeddings: OpenAIEmbeddings, llm: OpenAI, chat_manager: ChatManager) -> None:
        self.namespace = namespace
        self.index_name = index_name
        self.embeddings = embeddings
        self.llm = llm
        self.chat_manager = chat_manager
        
        self.qa = self.make_chain(self.get_vector_store())
        
    def get_vector_store(self) -> Pinecone | None:
        try:
            return Pinecone.from_existing_index(
                self.index_name,
                self.embeddings,
                namespace=self.namespace,
            )
        except Exception as e:
            print(e)

    def make_chain(self, vectorstore: Pinecone):
        return ConversationalRetrievalChain.from_llm(
            retriever=vectorstore.as_retriever(),
            llm=self.llm,
            return_source_documents=True,
        )

    def get_chat_history(self):
        return self.chat_manager.retrieve_all_messages(self.namespace)
        
    def add_message_to_db(self, ai_message: str, human_message: str) -> None:
        self.chat_manager.add_message(self.namespace, ai_message, human_message)
        
    def chat(self, message: str) -> str:
        print(message)
        result = self.qa({"question": message, "chat_history": self.get_chat_history()})
        output = result['answer']
        print(result['source_documents'])
        self.add_message_to_db(output, human_message=message)
        return output
