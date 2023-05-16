import steamship
from steamship import Steamship, File, Block, Tag, DocTag
from steamship.data.tags import TagKind
from steamship.data.tags.tag_constants import RoleTag

steamship = Steamship
gpt4 = Steamship.use_plugin("gpt-4")
# gpt4 = steamship.use_plugin("gpt-4", config={"max_tokens":1024})
# result_task = gpt4.generate(text="What's up GPT? please tell me a limerick")
# result_task.wait()


gpt4 = steamship.use_plugin("gpt-4")
client = gpt4.client

chat_file = File.create(client, blocks=[
    Block(
        text="You are an assistant who likes to tell jokes about bananas",
        tags=[Tag(kind=TagKind.ROLE, name=RoleTag.SYSTEM)]
    )
])
chat_file.append_block(
    text="Do you know any fruit jokes?",
    tags=[Tag(kind=TagKind.ROLE, name=RoleTag.USER)]
)
task = gpt4.generate(
    input_file_id=chat_file.id,
    append_output_to_file=True,
    output_file_id=chat_file.id
)
task.wait()
joke = task.output.blocks[0].text

print(joke)

# ai_package = Steamship.use(workspace="gpt4-sw-test-0")
# Create a Steamship client
# NOTE: When developing a package, just use `self.client`
# client = Steamship(workspace="gpt-4-demo")
# client.
# something = Steamship.
# Create an instance of this generator
# generator = client.use_plugin('gpt-4')

# open context.txt and read the contents
# context = ""
# with open("context.txt") as f:
#    context = f.read()

# question = "Summarize these modules document, then from this context, generate a class in the same pattern as the others" \
#           "that can be used to interpolate between two latents. don't forget imports and a test function, " \
#           "and also the init.py "
# question = "does it mention chat gpt? or chat models?"

# context = f"{question}\nQUESTION: {context}"
# Generate text
# task = generator.generate(text=context)

# Wait for completion of the task.
# task.wait()

# Print the output
# print(task.output.blocks[0].text)
