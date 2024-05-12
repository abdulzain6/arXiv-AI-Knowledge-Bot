import pinecone 

def initialize_pinecone(api_key: str, environment: str) -> None:
    pinecone.init(
        api_key=api_key,
        environment=environment 
    )


        

