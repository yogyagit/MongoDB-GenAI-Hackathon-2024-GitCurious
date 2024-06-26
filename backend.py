##nomic-embed-code

# ---
# args: ["--query", "How many oil barrels were released from reserves"]
# ---
# # Question-answering with LangChain
#
# In this example we create a large-language-model (LLM) powered question answering
# web endpoint and CLI. Only a single document is used as the knowledge-base of the application,
# the 2022 USA State of the Union address by President Joe Biden. However, this same application structure
# could be extended to do question-answering over all State of the Union speeches, or other large text corpuses.
#
# It's the [LangChain](https://github.com/hwchase17/langchain) library that makes this all so easy. This demo is only around 100 lines of code!

# ## Defining dependencies
#
# The example uses three PyPi packages to make scraping easy, and three to build and run the question-answering functionality.
# These are installed into a Debian Slim base image using the `pip_install` function.
#
# Because OpenAI's API is used, we also specify the `openai-secret` Modal Secret, which contains an OpenAI API key.

# A `docsearch` global variable is also declared to facilitate caching a slow operation in the code below.
from pathlib import Path
import modal
from modal_image import image, stub
from modal import Image, Secret, Stub, web_endpoint, Volume, asgi_app
from generate_documentation import CohereChatbot
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from atlas import AtlasClient
from NomicCls import NomicEmbeddings
from query_responder import QueryResponder
import nomic
from nomic import embed

web_app = FastAPI()

volume = Volume.from_name(
    "repo_data", create_if_missing=True
)

chatbot = CohereChatbot()
#nomicObj = NomicEmbeddings()
mongoDbClient =  AtlasClient()
queryResponder=QueryResponder()

@web_app.post("/get_response_endpoint")
async def get_response(request: Request):
    print("Recieved user query in backend")
    data = await request.json()
    user_input = data.get('user_query')
    chat_history = data.get("chat_history")
    print(chat_history)
    #mongoDbClient.empty_collection.remote(collection_name = "MongoHackCollection", database_name = 'MongoHack')
    transcript = []
    for message in chat_history:
        temp_dict = {}
        temp_dict['role'] = message['name']
        temp_dict['message'] = message['content']
        transcript.append(temp_dict)
    print(transcript)
    print("Creating user query embeddings")
    #chat_history = data.get('chat_history')
    #query_embeddings = nomicObj.get_query_embeddings.remote(user_input)
    query = [user_input]
    query_embeddings = chatbot.create_embeddings.remote(doc = query, input_type = "search_query").tolist()
    
    print("Sending the data for response from LLM")
    llm_output = queryResponder.generate_response.remote(user_input, query_embeddings, transcript)
    print(llm_output)
    return {"response": llm_output}
    
@web_app.post("/get_git_data")
async def get_git_data_endpoint(request: Request):
    print("Recieved URL at get_git_data")
    data = await request.json()
    github_url = data.get('github_url')
    if ".git" not in github_url:
        github_url = github_url + ".git"
    print('AG: inside get_git_data_endpoint.. redirecting to get_git_data')
    git_contents = get_git_data.remote(github_url)
    print("Sending for creating documentation")
    # Pass the code of each file to the LLm to get documentation for the code
    print(git_contents)
    
    
    for i, file in enumerate(git_contents):
        # Assuming generate_documentation.remote() returns a future or promise
        future = chatbot.generate_documentation.remote(file)
        git_contents[i]['documentation'] = [str(future)]
        print([str(future)])
        
    print('AG: done generate documentation...')
    #git_contents = nomicObj.get_doc_embeddings.remote(git_contents)
    for i, file in enumerate(git_contents):
        git_contents[i]['doc_embedding'] = chatbot.create_embeddings.remote(doc = git_contents[i]['documentation'], input_type = "search_document").tolist()

    print("Starting the insert process")
    mongoDbClient.insert_documents.remote(collection_name = "MongoHackCollection", database_name = 'MongoHack', documents = git_contents)
    print('AG: push done...')

@stub.function(image=image,
                volumes={'/data': volume},
                secrets=[modal.Secret.from_name("nomic-key")],
                )
def get_git_data(github_url):
    import subprocess
    import os
    import nomic
    from nomic import embed

    print('AG: inside get_git_data @stub.funtion')
    # Run the git clone command
    print(f'AG: starting git clone {github_url}')
    subprocess.run(f"cd /data && git clone {github_url}", shell=True)
    volume.commit()
    # Git content is list of dicts. Each element of list is a git file
    # and each dict has keys: path and code
    git_content = []
    def read_file_content(directory):
        code_extensions = ['.py', '.js', '.cpp']  # Add more extensions as needed
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                _, file_extension = os.path.splitext(file_path)
                if file_extension in code_extensions:
                    file_dict = {}
                    file_dict['path'] = file_path
                    with open(file_path, 'r') as f:
                        file_dict['code'] = f.read()
                        print(f"AG: {read_file_content.__name__} Contents saved for {file_path}:")
                    git_content.append(file_dict)
    
    # Split the URL and extract the repository name without the '.git' extension
    repository_name = github_url.split('/')[-1][:-4]
    # Use f-string to include the variables in the command
    subprocess.run(f"echo AG1234 && echo /data/{repository_name}", shell=True)
    read_file_content(f'/data/{repository_name}')
    print(f"Num of files read: {len(git_content)}")
    sample_file_data = """
        Once upon a time, in a quaint little town nestled between rolling hills and lush forests, there lived a friendly and adventurous dog named Max. Max was a mix of a Golden Retriever and a Border Collie, which made him both clever and affectionate.
        Max's days were filled with excitement and exploration. He would often roam the town, making friends with everyone he met. His favorite spot was the town square, where he would eagerly greet the townspeople and play with the local children.
        One day, while exploring the woods on the outskirts of town, Max stumbled upon a hidden path that led to a mysterious old house. Curiosity piqued, he bravely ventured inside, only to discover that the house was home to a family of friendly squirrels.
        The squirrels welcomed Max with open arms (or rather, open paws), and they quickly became the best of friends. Together, they would explore the woods, play games, and share stories late into the night.
        As the seasons changed, so did Max's adventures. In the winter, he would frolic in the snow with his squirrel friends, while in the summer, they would swim in the nearby creek and bask in the warm sun.
        Through his adventures, Max taught the townspeople the importance of kindness, friendship, and the joy of exploring the world around them. And so, Max's story became a beloved tale in the town, inspiring everyone to embrace life with the same enthusiasm and curiosity as their furry friend."""
    print('AG: git clone done')
    return git_content 

@stub.function(image=image,
                volumes={'/data': volume},
                )
#def generate_response(query_embedding, chat_history):
def generate_response(query_embedding):
    relevant_documents = mongoDbClient.vector_search.remote(
        database_name = 'MongoHack',
        collection_name='MongoHackCollection',
        index_name='vector_index_github',
        embedding_vector=query_embedding[0]
    )

    return relevant_documents
    """context = ""
    for doc in relevant_documents:
        context += doc['documentation'] + "\n" + doc['code'] + "\n\n"

    # Append example query-response pairs and updated instructions
    context += 
    Instructions for generating responses:
    - You have access to relevant documentation and code content related to the user's query about GitHub codespaces.
    - Generate a detailed and informative response that directly answers the user's query.
    - Use clear and technical language appropriate for a software developer.
    - Provide explanations, examples, or references to the provided documentation and code when necessary to clarify your response.
    - If the query is about a specific function or class, describe its purpose, usage, and any important parameters or return values.
    - If the query is about an error or issue, provide a possible explanation or solution based on the available code and documentation.
    - Ensure that your response is informative and helpful for someone working with GitHub codespaces.
    - If the query is unclear or lacks context, ask for clarification or additional information.
    

    response = self.chatbot.chat(message=context, chat_history=chat_history)
    return response"""

@stub.function(image=image,
                volumes={'/data': volume},
                secrets=[modal.Secret.from_name("nomic-key")],
                )
@asgi_app()
def fastapi_app():
    print('AG: starting fastapi app...')
    return web_app