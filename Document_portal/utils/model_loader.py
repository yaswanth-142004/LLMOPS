from langchain_google_genai import GoogleGenerativeAIEmbeddings 
from langchain_google_genai import ChatGoogleGenerativeAI 
from langchain_groq import ChatGroq 
from langchain_openai import ChatOpenAI
from logger.custom_logger import CustomLogger 
import os 
from dotenv import load_dotenv
from utils.config_loader import load_config 
from exception.custom_exception import DocumentPortalException 
import sys

logger = CustomLogger().get_logger(__name__)

class ModelLoader:
    def __init__(self):
        load_dotenv()
        self.validate_env()
        self.config = load_config() 
        logger.info("configuration loaded successfully", config_keys=list(self.config.keys()))
        
        
        
        
        
        
        
    def validate_env(self):
        """
        Validate necessary environment variables  
        
        Ensure API Keys exist 
        """
        
        required_vars=["GOOGLE_API_KEY"]
        provider = os.getenv("LLM_PROVIDER", "google")
        if provider == "groq":
            required_vars.append("GROQ_API_KEY")
        elif provider == "inferx":
            required_vars.append("INFERX_API_KEY")
        self.api_keys={key:os.getenv(key) for key in required_vars}
        missing = [k for k,v in self.api_keys.items() if not v]
        if missing:
            logger.error("Missing environemnt variables",missing_vars=missing)
            raise DocumentPortalException("Missing environemtal variables",sys)
        logger.info("Environmental variables validated",available_keys=[k for k in self.api_keys if self.api_keys[k]])
        
    def load_embeddings(self):
        """
        Load and return the embedding model 
        
        """ 
        
        try:
            logger.info("Loading the embedding model>>>")
            model_name = self.config["embedding_model"]["model_name"]
            return GoogleGenerativeAIEmbeddings(model=model_name)
        except Exception as e:
            logger.error("Error loading embedding model",error=str(e))
            raise DocumentPortalException("Failed to load Embedding model ",sys)
    
    def load_llm(self):
        """Load and return the LLM Model """
        
        llm_block = self.config['llm']
        
        logger.info("Loading the LLM >>>>>>>")
        
        provider_key = os.getenv("LLM_PROVIDER","google")
        
        if provider_key not in llm_block:
            logger.error("LLM Provider not founf in the cconfig ",provider_key=provider_key)
            raise ValueError(f"Provider '{provider_key}' not found in config")
        
        llm_config = llm_block[provider_key]
        provider = llm_config.get("provider")
        model_name = llm_config.get("model_name")
        temperature =  llm_config.get("temperature")
        max_tokens = llm_config.get("max_output_tokens",2048)
        
        logger.info("Loading LLM", provider=provider, model=model_name, temperature=temperature, max_tokens=max_tokens)
        
        if provider == "google":
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                max_output_tokens = max_tokens
            )
            
            return llm 
        
        elif provider == "groq":
            llm = ChatGroq(
                model=model_name,
                api_key=self.api_keys["GROQ_API_KEY"],
                temperature=temperature
            )
            
            return llm

        elif provider == "inferx":
            llm = ChatOpenAI(
                model=model_name,
                api_key=self.api_keys["INFERX_API_KEY"],
                base_url=llm_config.get("api_base", "https://model.inferx.net/endpoints/v1"),
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return llm
        
        else:
            logger.error("Unsupported LLM Provider",provider=provider)
            raise ValueError("Unsupported LLM Provider ",{provider})
        
        
if __name__ == "__main__":
    loader = ModelLoader()
    
    embeddings = loader.load_embeddings()
    
    print(f"Embedding Model Loaded : {embeddings}")
    
    #test the embedding model 
    
    result = embeddings.embed_query("This Is Yaswanth")
    print(f"Embedding result :{result}")
    
    
    llm = loader.load_llm()
    print(f"LLM Loaded succesfully")
    
    
    result = llm.invoke("what is AI")
    print(f"LLM Result :{result.content}")
    