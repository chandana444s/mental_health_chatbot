from langchain.chains import LLMChain
from langchain.llms import OpenAI

llm = OpenAI(model="text-davinci-003")
chain = LLMChain(llm=llm)
response = chain.run("What is LangChain?")
print(response)
