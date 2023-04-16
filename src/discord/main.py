import subprocess

import discord
from discord import Option

from file_path_mgr import private_ini

DISCORD_SERVER_IDs = private_ini("discord", "DISCORD_SERVER_ID").split(',')
DISCORD_SERVER_IDs = list(map(int, DISCORD_SERVER_IDs))

TOKEN = str(private_ini("discord", "TOKEN"))
client = discord.Bot()
 
@client.event
async def on_ready():
    print(f"{client.user} WAITING CMD...")


@client.slash_command(description="当日スクレイピング", guild_ids=DISCORD_SERVER_IDs)
async def scraping2(
    ctx: discord.ApplicationContext,
    race_id: Option(str, required=True, description="input race_id"),
    skip_login: Option(bool, required=False, description="skip netkeiba login")

):
    # スクレイピングのみ
    await ctx.respond("scraping will start")
    scraping_cmd = ['python', './src/scraping/netkeiba_scraping2.py', '--race_id', race_id]

    if skip_login:
        scraping_cmd.append('--skip_login')

    await exe_cmd(ctx, scraping_cmd)


@client.slash_command(description="当日レース予想", guild_ids=DISCORD_SERVER_IDs)
async def predict(
    ctx: discord.ApplicationContext,
):
    # 推測のみ
    await ctx.respond("predict will start")
    predict_cmd = ['python', './src/deepLearning/nn/predict.py']
    await exe_cmd(ctx, predict_cmd)

@client.slash_command(description="バッチ実行", guild_ids=DISCORD_SERVER_IDs)
async def bat(
    ctx: discord.ApplicationContext,
    race_id: Option(str, required=True, description="input race_id")
):
    await ctx.respond("scraping will start")
    scraping_cmd = ['predict.bat', '--race_id', race_id]
    await exe_cmd(ctx, scraping_cmd)

async def exe_cmd(ctx, cmd_list):
    stdout_log = [' '.join(cmd_list) + '\n']
    for line in get_lines(cmd_list):
        stdout_log.append(line)
        
        # discord の一度の送信できる文字数は2000文字
        # 余裕を持って1500文字以上なら古い行から削除していく
        cout = ''.join(stdout_log)

        while len(cout) > 1500:
            del stdout_log[1]
            cout = ''.join(stdout_log)

        await ctx.edit(content=cout)
    await ctx.edit(content=(cout + "NEXT CMD READY\n"))

def get_lines(cmd):
    '''
    :param cmd: str 実行するコマンド.
    :rtype: generator
    :return: 標準出力 (行毎).
    '''
    proc = subprocess.Popen(cmd, encoding='shift-jis', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while True:
        
        line = proc.stdout.readline()
        if line:
            print(line, end='')
            yield line

        if not line and proc.poll() is not None:
            print("subprocess Popen comp")
            break

if __name__ == '__main__':
    client.run(TOKEN)
