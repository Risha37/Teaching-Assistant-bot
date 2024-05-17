from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain.memory import ConversationBufferMemory
from langchain.chains import RetrievalQA

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma


# =============================================================================


def get_retriever(pdf_file: str
                  ):
    """
    Description
    ----------
    Processes a PDF file, generates embeddings for each page, 
    and stores these embeddings in an in-memory search structure.

    Key Parameters
    ----------
    pdf_file : str
        The path to the PDF file to be processed.

    Returns
    ----------
    retriever : VectorStoreRetriever
        A retriever object for querying the embeddings of the PDF pages.
    """
    loader = PyPDFLoader(pdf_file)
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorstore = Chroma.from_documents(texts, embeddings)
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k":2})
    return retriever


# =============================================================================


def get_prompt_template(age: int,
                        name: str,
                        use_case: str=None
                        ) -> str:
    """
    Description
    ----------
    Generates a prompt template for the chatbot based on the age and name of the user.

    Key Parameters
    ----------
    age : int
        The age of the user.
    name : str
        The name of the user.

    Returns
    ----------
    prompt_template : str
        A string that represents the prompt template for the chatbot.
    """

    if use_case == "test":
        prompt_template ="""
            **You are a teacher for Arabic-speaking children.**

            **Instructions:**
                As the PDF Reader Expert, your goal is to assist children by only generating 5 multiple choice questions that are appropriate for a %d-year-old child as a JSON regarding the context:
                - The kid is %d-year-old, so keep the language simple and easy to understand and their name is "%s".
                - Only respond in Arabic and nothing else.
                - Return the questions as JSON only which contains the (question, options, correct_answer) and don't use any formatting and the options max number is 4.
            
            **Context:**
            {context}

            {question}
            **Answer:**
        """.strip() % (age, age, name)

    elif use_case == "explain":
        prompt_template ="""
            **You are a teacher for Arabic-speaking children.**

            **Instructions:**
                As the PDF Reader Expert, your goal is to assist children by providing explanations in Arabic from the context of the provided PDF, and nothing outside of it:
                - The kid is %d-year-old, so keep the language simple and easy to understand and their name is "%s".
                - Be chatty, kind, friendly and patient with the child.
                - Only respond in Arabic and nothing else.
                - explain the lecture (context), and present the information in an engaging and fun manner suitable for a %d-year-old child.
                - The Answer should not exceed 150 words.
                - Don't make it a story.

            **Context:**
            {context}

            {question}
            **Answer:**
        """.strip() % (age, name, age)

    else:
        prompt_template ="""
            **You are a teacher for Arabic-speaking children.**

            **Instructions:**
                As the PDF Reader Expert, your goal is to assist children by providing explanations in Arabic from the context of the provided PDF, and nothing outside of it:
                - The Answer should not exceed 100 words.
                - The kid is %d-year-old, so keep the language simpleshort, and easy to understand and their name is "%s".
                - Be chatty, kind, friendly and patient with the child.
                - Only respond in Arabic and nothing else.
                - Don't generate any questions.
                - If asked outside the context of the PDF, respond with "الرجاء عدم الخروج عن سياق الدرس"
                - If there's no context, forget everything and act as a normal chatbot.

            **Context:**
            {context}
            
            **Chat History:**:
            {history}

            **Question:**
            {question}

            **Answer:**
        """.strip() % (age, name)
    return prompt_template


# =============================================================================


def generate_response(age: int,
                      name: str,
                      user_question: str,
                      tmp_path: str,
                      use_case: str=None
                      ):
    """
    Description
    ----------
    Generates a response from the chatbot based on the user's question and the content of a PDF file.

    Key Parameters
    ----------
    age : int
        The age of the user.
    name : str
        The name of the user.
    user_question : str
        The question asked by the user.
    tmp_path : str
        The path to the PDF file to be processed.

    Returns
    ----------
    response : str
        The response generated by the chatbot.
    """
    retriever = get_retriever(tmp_path)

    memory = ConversationBufferMemory(memory_key="history", input_key="question")
    print(memory.load_memory_variables({}))

    if use_case == "test":
        prompt_template = get_prompt_template(age, name, use_case=use_case)
        prompt = PromptTemplate(template=prompt_template,
                                input_variables=["context", "question"]
                                )
        user_question = "test"
        
    elif use_case == "explain":
        prompt_template = get_prompt_template(age, name, use_case=use_case)
        prompt = PromptTemplate(template=prompt_template,
                                input_variables=["context", "question"]
                                )
        user_question = "explain"
    
    else:
        prompt_template = get_prompt_template(age, name, use_case=use_case)
        prompt = PromptTemplate(template=prompt_template,
                                input_variables=["history", "context", "question"]
                                )
    
    llm = ChatGoogleGenerativeAI(model="gemini-pro",
                                 temperature=0,
                                 maxOutputTokens=1024,
                                 safety_settings=None
                                 )
    
    retrieval_chain = RetrievalQA.from_chain_type(llm,
                                                  chain_type='stuff',
                                                  retriever=retriever, 
                                                  chain_type_kwargs={"prompt": prompt,
                                                                     "memory": memory}
                                                 )
    response = retrieval_chain.run(user_question)
    return response


# =============================================================================