import os
import time
from openai import AzureOpenAI

os.environ["AZURE_OPENAI_ENDPOINT"] = ""
os.environ["AZURE_OPENAI_API_KEY"] = ""

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
deployment = "sihChatBot"  # Your new deployment name

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version="2024-02-15-preview"
)

def hr_chatbot(user_input):
    hr_context = ("Answer this as an HR of a big SaaS company, give replies specific to your company, not generic. "
                  "You should know everything about HR policy and rules. Give answers in paragraphs, not points.\n\n, reply with as short answer as possible, but it should make sense")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            completion = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": hr_context},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=800,
                temperature=0.7,
                top_p=0.95,
            )
            end_time = time.time()
            print(f"API call took {end_time - start_time:.2f} seconds")
            return completion.choices[0].message.content
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed. Retrying...")
                time.sleep(1)  # Wait for 1 second before retrying
            else:
                return f"An error occurred: {str(e)}"

print("HR Chatbot: Hello! I'm here to help with any questions. Type 'exit' to end the conversation.")

while True:
    user_input = input("You: ")
    if user_input.lower() == 'exit':
        print("HR Chatbot: Thank you for using our service. Goodbye!")
        break
    response = hr_chatbot(user_input)
    print("HR Chatbot:", response)
