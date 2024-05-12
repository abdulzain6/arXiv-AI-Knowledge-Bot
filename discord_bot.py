import asyncio
import os
import discord
from openai_utils import add_pdf_to_memory, summarize_pdf, ChatRetrievalWithDB
from discord.ext import commands
from arxiv_scraper import ArxivScraper
from globals import (
    channel_name,
    database_manager,
    monitor_interval,
    creds,
    chat_manager,
    config,
)
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chat_models import ChatOpenAI
from components import NewPDF
from utils import download_pdf, create_pdf_embed, embeded_text
import asyncio


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.heartbeat_timeout = 900
started = False







async def check_for_pdfs():
    while True:
        try:
            print("Checking for pdfs")
            scraper = ArxivScraper("history_file.txt", 2, "selectors.json")
            channel = discord.utils.get(bot.get_all_channels(), name=channel_name)
            new_pdfs = await scraper.start(days_limit=2, pdf_limit=5)
            print("Scrape done")
            await asyncio.sleep(5)

            print(f"New PDFS {len(new_pdfs)}")
            
            if len(new_pdfs) <= 0:
                continue

            await channel.send(
                embed=embeded_text(f"{len(new_pdfs)} new PDFs Found!", "Information")
            )
            for pdf in new_pdfs:
                await channel.send(
                    embed=embeded_text(pdf["title"], ":star: New Item!"),
                    view=NewPDF(pdf_url=pdf["link"], pdf_file_path=pdf["file_path"], title=pdf["title"], bot=bot),
                )
            await asyncio.sleep(monitor_interval)
                
        except Exception as e:
            print(e)


@bot.event
async def on_ready():
    global started
    print(
        f"{bot.user.name} has connected to Discord! Type !commands for the commands list"
    )
    channel = discord.utils.get(bot.get_all_channels(), name=channel_name)
    
    if not started:
        await channel.send(
            embed=embeded_text(
                "ChatArxiv bot has entered the chat! Type !commands for the commands list",
                "",
            )
        )
        started = True

    #await check_for_pdfs()
    bot.loop.create_task(check_for_pdfs())


@bot.command(name="choose")
async def choose(ctx, message):
    channel = discord.utils.get(bot.get_all_channels(), name=channel_name)
    pdfs = database_manager.get_all_pdfs()
    global chosen_pdf_name
    try:
        index = int(message)
        chosen_pdf = pdfs[index - 1]
        chosen_pdf_name = str(chosen_pdf.pdf_name)
        await channel.send(
            embed=embeded_text(f"You have chosen {chosen_pdf.pdf_title}", "PDF Chosen!")
        )
    except Exception:
        await channel.send(
            embed=embeded_text(
                f"Invalid Value chosen, Choose from 1-{len(pdfs)}", "Wrong Value!"
            )
        )
        return


@bot.command(name="describe")
async def describe(ctx, message: str):
    channel = discord.utils.get(bot.get_all_channels(), name=channel_name)
    filepath = os.path.join("pdfs", message.split("/")[-1])
    await download_pdf(message, filepath)
    namespace, pages = add_pdf_to_memory(filepath)
    database_manager.create_pdf_file(namespace, filepath, message.split("/")[-1])
    embed = create_pdf_embed(
        summary=summarize_pdf(pages),
        link=message,
        title=message.split("/")[-1],
        description="Pdf SUmmary",
    )
    await channel.send(embed=embed)


@bot.command(name="list")
async def list(ctx):
    channel = discord.utils.get(bot.get_all_channels(), name=channel_name)
    pdfs = database_manager.get_all_pdfs()
    embed = discord.Embed(title="Available PDFs")
    for i, pdf in enumerate(pdfs, start=1):
        try:
            name = f"{i}. {pdf.pdf_title} ({pdf.pdf_name.split('__')[1]})"
        except Exception as e:
            name = f"{i}. {pdf.pdf_title}"
        embed.add_field(
            name=name,
            value="\u200b",
            inline=False,
        )

    await channel.send(embed=embed)


@bot.command(name="commands")
async def commands(ctx):
    channel = discord.utils.get(bot.get_all_channels(), name=channel_name)
    embed = discord.Embed(title="Available Commands")
    embed.add_field(
        name="1. list",
        value="Lists All the available PDFs",
        inline=False,
    )
    embed.add_field(
        name="2. choose",
        value="Allows the user to choose a PDF",
        inline=False,
    )
    embed.add_field(
        name="2. chat",
        value="Allows the user to chat with the PDF",
        inline=False,
    )
    embed.add_field(
        name="4. describe",
        value="Downloads a pdf from a link and adds it to the database",
        inline=False,
    )
    await channel.send(embed=embed)


@bot.command(name="chat")
async def chat(ctx, *message):
    channel = discord.utils.get(bot.get_all_channels(), name=channel_name)
    pdf = database_manager.get_pdf_by_name(chosen_pdf_name)
    if not pdf:
        await channel.send(
            embed=embeded_text("Please choose a PDF using !choose", "No PDF available")
        )

    chat = ChatRetrievalWithDB(
        pdf.namespace,
        creds["INDEX_NAME"],
        HuggingFaceEmbeddings(),
        ChatOpenAI(
            openai_api_key=creds["OPENAI_API_KEY"],
            model_name=config["MODEL_NAME"],
            temperature=0,
        ),
        chat_manager,
    )
    await channel.send((chat.chat(" ".join(message))))


if __name__ == "__main__":
    bot.run(creds["BOT_TOKEN"])
