import discord
import json
import os
import sys
from discord.ext.commands import command, has_permissions, bot_has_permissions, Bot, NotOwner
from asyncio import sleep

CONFIG_PATH = "config.json"
default_config = {
        "token": "[ add bot token here ]",
        "developers": [],
        "prefix": "^",
        "mod_role": 0,
        "blacklist": [],
        "mail_channel": 0,
        "from_field": 1,
}

class ModmailBot(object):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.last_user = None

    async def on_ready(self):
        print(f"Signed in as {self.bot.user} ({self.bot.user.id})")
    async def on_message(self, message):
        if not isinstance(message.channel, discord.DMChannel) or message.author.id == self.bot.user.id:
            # not a DM, or it's just the bot itself
            return
        channel = self.bot.get_channel(self.config["mail_channel"])
        if not channel:
            print("Mail channel not found! Reconfigure bot!")
        
        content = message.clean_content

        embed = discord.Embed(title="New modmail!")
        embed.add_field(name="Author", value=f"{message.author.mention} ({message.author.id})", inline=False)
        embed.add_field(name="Message", value=content[:1000] or "blank")
        if message.attachments:
            embed.add_field(name="Attachments", value=", ".join([i.url for i in message.attachments]))
        if len(content[1000:]) > 0:
            embed.add_field(name="Message (continued):", value=content[1000:])
        await channel.send(content=f"{message.author.id}", embed=embed)
        await message.add_reaction('📬')
        self.last_user = message.author

    async def _shutdown(self):
        await self.bot.logout()
        await self.bot.close()
        self.bot.loop.stop()
    
    @command()
    async def dm(self, ctx, user : discord.User, *, msg):
        if ctx.channel.id != self.config["mail_channel"]:
            return
        if self.config["from_field"]:
            await user.send(f"From {ctx.author.display_name}: {msg}")
        else:
            await user.send(msg)
        await ctx.message.add_reaction('📬')

    @command()
    async def reply(self, ctx, *, msg):
        if self.last_user is None:
            await ctx.send("No user to reply to!")
            return
        await self.dm.callback(self, ctx, user=self.last_user, msg=msg)
    @command()
    async def reee(self, ctx, user : discord.User, times : int, *, msg):
        if ctx.author.id not in config["developers"]:
            return
        with ctx.typing():
            for i in range(times):
                if self.config["from_field"]:
                    await user.send(f"From {ctx.author.display_name}: {msg}")
                else:
                    await user.send(msg)
                await sleep(1.25)
            await ctx.message.add_reaction('📬')


    @command()
    async def shutdown(self, ctx):
        if ctx.author.id not in config["developers"]:
            return

        await ctx.send('Shutting down...')
        await self._shutdown()

    @command()
    async def restart(self, ctx):
        if ctx.author.id not in config["developers"]:
            return

        await ctx.send('Restarting...')
        await self._shutdown()
        script = sys.argv[0]
        if script.startswith(os.getcwd()):
            script = script[len(os.getcwd()):].lstrip(os.sep)

        if script.endswith('__main__.py'):
            args = [sys.executable, '-m', script[:-len('__main__.py')].rstrip(os.sep).replace(os.sep, '.')]
        else:
            args = [sys.executable, script]
        os.execv(sys.executable, args + sys.argv[1:])


def write_config(config: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent="\t")

def read_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

if not os.path.exists(CONFIG_PATH):
    write_config(default_config)
    print("No config detected; a new one has been written! Please edit config.json then run the bot again.")
    sys.exit(1)

config = read_config()
bot = Bot(config["prefix"], description="A modmail bot.")
bot.add_cog(ModmailBot(bot, config))
bot.run(config["token"])
