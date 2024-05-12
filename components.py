import discord
from openai_utils import add_pdf_to_memory, summarize_pdf
from globals import database_manager, channel_name
from utils import create_pdf_embed, embeded_text


class NewPDF(discord.ui.View): 
    def __init__(self, *, timeout: float | None = None, pdf_url: str, pdf_file_path: str, title: str, bot):
        super().__init__(timeout=timeout)
        button = discord.ui.Button(label="Read PDF", style=discord.ButtonStyle.gray, emoji="📃", url=pdf_url)
        self.add_item(button)
        self.pdf_file_path = pdf_file_path
        self.bot = bot
        self.pdf_url = pdf_url
        self.title = title
        
        
    @discord.ui.button(label="Add To Pinecone", style=discord.ButtonStyle.green, emoji="🌲") 
    async def add_pinecone(self, interaction: discord.Interaction, button):
        channel = discord.utils.get(self.bot.get_all_channels(), name=channel_name)
        await channel.send(embed=embeded_text(f"Adding {self.title} to pinecone..", "Information")) 
        
        button.disabled = True 
        button.label = "Adding to Pinecone" 
        await interaction.response.edit_message(view=self) 
        
        
        namespace, pages = add_pdf_to_memory(self.pdf_file_path)
        database_manager.create_pdf_file(
            namespace, self.pdf_file_path, self.pdf_file_path.split("__")[2][:-4]
        )
        embed = create_pdf_embed(
            summary=summarize_pdf(pages), link=self.pdf_url, title=self.title
        )
        
        await channel.send(embed=embed) 



