import json
import discord
import httpx
import jsonschema
from jsonschema import validate
from typing import Dict


def validate_json(jsondata: Dict, schema: Dict) -> bool:
    try:
        validate(instance=jsondata, schema=schema)
    except jsonschema.exceptions.ValidationError as err:
        return False
    return True

def load_credentials(filename="credentials.json") -> dict[str, str]:
    with open(filename, "r") as fp:
        return json.load(fp)


def load_config(filename="config.json") -> dict[str, str]:
    with open(filename, "r") as fp:
        return json.load(fp)
    
async def download_pdf(
     link: str, filename: str
) -> None:
        session = httpx.AsyncClient()   
        response = await session.get(link)
        with open(filename, "wb") as f:
            f.write(response.content)


def create_pdf_embed(
    summary: str,
    link: str,
    title: str,
    description: str = "A new PDF was posted on arxiv.",
) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        url=link,
        description=description,
        color=0x074B6C,
    )
    embed.add_field(name="Title", value=title, inline=True)
    embed.add_field(name="Summary", value=summary, inline=True)
    return embed

def embeded_text(string: str, title: str) -> discord.Embed:
    embed = discord.Embed(title=title)
    embed.add_field(name=string, value="\u200b", inline=False)
    return embed

