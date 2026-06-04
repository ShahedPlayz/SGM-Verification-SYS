# ╔══════════════════════════════════════════════════════════════════════════╗
# ║         SGM Verify SyS — Ultimate Verification System v6.1 (FIXED)       ║
# ║              Environment-Aware • Self-Healing • Production               ║
# ║                      Made with ❤️ • by SGM Company                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# ================================ IMPORTS ===============================
import discord
from discord.ext import commands, tasks
from discord.ui import View
import json
import asyncio
from datetime import datetime
import aiohttp

# ============ BOT TOKEN ============
TOKEN = 'YOUR_BOT_TOKEN'  # Replace with your bot's token

# ============ CHANNEL CONFIGURATION ============
VERIFY_CHANNEL_ID = 0000000000000000000  # Channel where the main verification button is located (can be in any guild, but usually in main guild)
REQUEST_CHANNEL_ID = 0000000000000000000 # Channel where verification requests are sent for handlers to accept/decline (should be in REMOTE_GUILD_ID)
CONTROL_PANEL_CHANNEL_ID = 0000000000000000000 # Channel where the control panel (emergency, view, auto-accept) is located (should be in REMOTE_GUILD_ID, can be same as request channel)
LOG_CHANNEL_ID = 0000000000000000000 # Channel where all verification actions are logged (should be in REMOTE_GUILD_ID, can be same as request channel)
# ============ GUILD CONFIGURATION ============
MAIN_GUILD_ID = 0000000000000000000  # Main guild where verification happens and roles are managed
REMOTE_GUILD_ID = 0000000000000000000  # Guild for request, control panel, and log channels

# ============ ROLE CONFIGURATION ============
DOUBLE_VERIFICATION_PREVENTION_ROLES = [
    # If user has ANY of these roles, they are considered already verified
    # Add role IDs here to prevent double verification
    0000000000000000000,  # Example: Verified Role
    # Add as many roles as you want
]

ROLES_ADD_ON_VERIFY = [
    0000000000000000000,  # Role 1 (e.g., Member)
    0000000000000000000,  # Role 2 (e.g., Verified)
    # Add as many roles as you want - These roles are ADDED when user gets verified
]

ROLE_REMOVE_AFTER_VERIFY = [
    0000000000000000000,  # Role to remove after successful verification (e.g., Unverified)
    # Add as many roles as you want - These roles are REMOVED when user gets verified
]

ROLES_REMOVE_AUTO = [
    # Roles that will be removed during inactivity check (from verified members)
    0000000000000000000,  # Member role
    0000000000000000000,  # Verified role
    # Add as many roles as you want - These are REMOVED when user is inactive
]

ROLES_ADD_AUTO = [
    # Roles that will be added during inactivity check (to inactive members)
    0000000000000000000,  # Unverified role
    # Add as many roles as you want - These are ADDED when user becomes inactive
]

ROLES_REMOVE_MANUAL = [
    # Roles removed when EMS-TAKE button is pressed
    0000000000000000000,  # Member role
    0000000000000000000,  # Verified role
    # Add as many roles as you want
]

ROLES_ADD_MANUAL = [
    # Roles added when EMS-TAKE button is pressed
    0000000000000000000,  # Unverified role
    # Add as many roles as you want
]

# ============ IGNORED USERS CONFIGURATION ============
ROLES_IGNORE = [
    0000000000000000000,  # Default ignored user ID
    # Add as many user IDs as you want - these users won't be affected by role changes
]

# ============ SYSTEM CONFIGURATION ============
INACTIVITY_TIMEOUT_MINUTES = 2 # Time in minutes after which a verified user is considered inactive

# ============ DATA FILE CONFIGURATION ============
DATA_FILE = 'SGM-VerifyDB.json'


# ========================== CUSTOM EMOJIS CONFIG ==============================
_EMOJI_OBJECTS = []

def _emoji(name, animated=False):
    obj = discord.PartialEmoji(name=name, animated=animated)
    _EMOJI_OBJECTS.append(obj)
    return obj

EMOJI_CHECKMARK = _emoji("checkmark")
EMOJI_XMARK = _emoji("xmark")
EMOJI_WRENCH = _emoji("squarewrench")
EMOJI_STATS = _emoji("growthids")
EMOJI_WARNING = _emoji("warning")
EMOJI_BELL = _emoji("weddingbell")
EMOJI_CLIPBOARD = _emoji("clipboard")
EMOJI_CLOCK = _emoji("clock", animated=True)
EMOJI_SIREN = _emoji("siren")
EMOJI_LOCKED = _emoji("locked")
EMOJI_LOADING = _emoji("loading", animated=True)

# ======================== CUSTOM EMOJIS CONFIG END ============================



# ========================= YOU DONT HAVE TO EDIT ANYTHING BELOW THIS LINE UNLESS YOU KNOW WHAT YOU ARE DOING =========================
async def fetch_emoji_ids():
    headers = {"Authorization": f"Bot {TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://discord.com/api/v10/oauth2/applications/@me", headers=headers) as resp:
            app = await resp.json()
            app_id = app["id"]
        async with session.get(f"https://discord.com/api/v10/applications/{app_id}/emojis", headers=headers) as resp:
            data = await resp.json()
            emoji_data = {e["name"]: e for e in data.get("items", [])}
    for obj in _EMOJI_OBJECTS:
        if obj.name in emoji_data:
            e = emoji_data[obj.name]
            obj.id = int(e["id"])
            obj.animated = e.get("animated", False)
        else:
            print(f"[WARNING] Emoji '{obj.name}' not found in application emojis — upload it in Discord Developer Portal")
    print(f"[EMOJI] Fetched IDs for {sum(1 for o in _EMOJI_OBJECTS if o.id is not None)}/{len(_EMOJI_OBJECTS)} emojis")


class BotData:
    def __init__(self):
        self.requests = {}
        self.last_message_time = {}
        self.verified_since = {}
        self.auto_accept_enabled = False
        self.auto_uy_enabled = False
        self.load_data()

    def load_data(self):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                self.requests = data.get('requests', {})
                self.last_message_time = data.get('last_message_time', {})
                self.verified_since = data.get('verified_since', {})
                self.auto_accept_enabled = data.get('auto_accept_enabled', False)
                self.auto_uy_enabled = data.get('auto_uy_enabled', False)
        except FileNotFoundError:
            self.requests = {}
            self.last_message_time = {}
            self.verified_since = {}
            self.auto_accept_enabled = False
            self.auto_uy_enabled = False
            self.save_data()

    def save_data(self):
        with open(DATA_FILE, 'w') as f:
            json.dump({
                'requests': self.requests,
                'last_message_time': self.last_message_time,
                'verified_since': self.verified_since,
                'auto_accept_enabled': self.auto_accept_enabled,
                'auto_uy_enabled': self.auto_uy_enabled
            }, f, indent=4)

    def add_request(self, user_id):
        self.requests[str(user_id)] = {
            'status': 'pending',
            'timestamp': datetime.now().isoformat()
        }
        self.save_data()

    def update_request(self, user_id, status):
        if str(user_id) in self.requests:
            self.requests[str(user_id)]['status'] = status
            self.requests[str(user_id)]['timestamp'] = datetime.now().isoformat()
            self.save_data()

    def has_pending_request(self, user_id):
        return str(user_id) in self.requests and self.requests[str(user_id)]['status'] == 'pending'

    def update_last_message(self, user_id):
        current_time = datetime.now().isoformat()
        self.last_message_time[str(user_id)] = current_time
        self.save_data()

    def mark_verified(self, user_id):
        current_time = datetime.now().isoformat()
        self.verified_since[str(user_id)] = current_time
        self.save_data()

    def get_inactive_users(self, guild, timeout_minutes):
        inactive_users = []
        ignored_ids = {str(uid) for uid in ROLES_IGNORE}

        for role_id in ROLES_ADD_ON_VERIFY:
            verified_role = guild.get_role(role_id)
            if not verified_role:
                continue

            current_time = datetime.now()

            for member in verified_role.members:
                if member.bot or str(member.id) in ignored_ids:
                    continue

                if member in inactive_users:
                    continue

                uid = str(member.id)
                verified_since_str = self.verified_since.get(uid)

                if not verified_since_str:
                    continue

                verified_since = datetime.fromisoformat(verified_since_str)
                time_since_verified = (current_time - verified_since).total_seconds() / 60

                if time_since_verified < timeout_minutes:
                    continue

                last_msg_str = self.last_message_time.get(uid)

                if last_msg_str:
                    last_msg_time = datetime.fromisoformat(last_msg_str)
                    time_since_last_msg = (current_time - last_msg_time).total_seconds() / 60

                    if time_since_last_msg >= timeout_minutes:
                        inactive_users.append(member)
                else:
                    if time_since_verified >= timeout_minutes:
                        inactive_users.append(member)

        return inactive_users


def get_channel_global(bot, channel_id):
    """Search for channel in all guilds, prioritizing REMOTE_GUILD_ID"""
    # First check remote guild
    remote_guild = bot.get_guild(REMOTE_GUILD_ID)
    if remote_guild:
        channel = remote_guild.get_channel(channel_id)
        if channel:
            return channel
    
    # Then check all other guilds
    for guild in bot.guilds:
        channel = guild.get_channel(channel_id)
        if channel:
            return channel
    return None


def get_member_global(bot, user_id):
    """Get member from main guild"""
    main_guild = bot.get_guild(MAIN_GUILD_ID)
    if main_guild:
        member = main_guild.get_member(user_id)
        if member:
            return member, main_guild
    return None, None


def is_ignored_user(user_id):
    """Check if user is in the ignore list"""
    return user_id in ROLES_IGNORE


def is_already_verified(member):
    """Check if member has any of the double verification prevention roles"""
    if not member:
        return False
    
    for role_id in DOUBLE_VERIFICATION_PREVENTION_ROLES:
        role = member.guild.get_role(role_id)
        if role and role in member.roles:
            return True
    
    return False


class AutoAcceptView(View):
    def __init__(self):
        super().__init__(timeout=300)
        self.message = None

    async def update_display(self, interaction):
        bot_data = interaction.client.bot_data
        self.status = bot_data.auto_accept_enabled
        status_text = f"Enabled {EMOJI_CHECKMARK}" if self.status else f"Disabled {EMOJI_XMARK}"
        embed = discord.Embed(
            title=f"{EMOJI_LOCKED} Auto-Accept Configuration",
            description=f"> *Configure automatic request handling.*\n\n"
                       f"**Status:** {status_text}\n"
                       f"Toggle below to enable or disable auto-accept.",
            color=0x2b2d31,
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"{interaction.client.get_guild(MAIN_GUILD_ID).name if interaction.client.get_guild(MAIN_GUILD_ID) else 'Unknown'} • Auto-Accept System • 24/7 Active")
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except:
            try:
                await interaction.edit_original_response(embed=embed, view=self)
            except:
                pass

    @discord.ui.button(label="Enable", style=discord.ButtonStyle.green, custom_id="auto_accept_enable")
    async def enable_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot_data = interaction.client.bot_data
        bot_data.auto_accept_enabled = True
        bot_data.save_data()
        print(f"[AUTO-ACCEPT] Enabled by {interaction.user.name}")
        await self.update_display(interaction)

    @discord.ui.button(label="Disable", style=discord.ButtonStyle.red, custom_id="auto_accept_disable")
    async def disable_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot_data = interaction.client.bot_data
        bot_data.auto_accept_enabled = False
        bot_data.save_data()
        print(f"[AUTO-ACCEPT] Disabled by {interaction.user.name}")
        await self.update_display(interaction)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass


class AutoUYView(View):
    def __init__(self):
        super().__init__(timeout=300)
        self.message = None

    async def update_display(self, interaction):
        bot_data = interaction.client.bot_data
        self.status = bot_data.auto_uy_enabled
        status_text = f"Enabled {EMOJI_CHECKMARK}" if self.status else f"Disabled {EMOJI_XMARK}"
        embed = discord.Embed(
            title=f"{EMOJI_LOCKED} Auto-UY Configuration",
            description=f"> *Configure automatic unverification.*\n\n"
                       f"**Status:** {status_text}\n"
                       f"Inactivity threshold: {INACTIVITY_TIMEOUT_MINUTES}+ min.",
            color=0x2b2d31,
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"{interaction.client.get_guild(MAIN_GUILD_ID).name if interaction.client.get_guild(MAIN_GUILD_ID) else 'Unknown'} • Auto-UY System • 24/7 Active")
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except:
            try:
                await interaction.edit_original_response(embed=embed, view=self)
            except:
                pass

    @discord.ui.button(label="Enable", style=discord.ButtonStyle.green, custom_id="auto_uy_enable")
    async def enable_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot_data = interaction.client.bot_data
        bot_data.auto_uy_enabled = True
        bot_data.save_data()
        print(f"[AUTO-UY] Enabled by {interaction.user.name}")
        await self.update_display(interaction)

    @discord.ui.button(label="Disable", style=discord.ButtonStyle.red, custom_id="auto_uy_disable")
    async def disable_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot_data = interaction.client.bot_data
        bot_data.auto_uy_enabled = False
        bot_data.save_data()
        print(f"[AUTO-UY] Disabled by {interaction.user.name}")
        await self.update_display(interaction)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass


class VerifyView(View):
    def __init__(self, bot_data):
        super().__init__(timeout=None)
        self.bot_data = bot_data

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green, custom_id="verify_button_main")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        
        # Check if user is ignored
        if is_ignored_user(user.id):
            await interaction.response.send_message("You are exempt from verification.", ephemeral=True)
            return
        
        main_guild = interaction.client.get_guild(MAIN_GUILD_ID)

        if main_guild:
            member = main_guild.get_member(user.id)
            if member:
                # Check if user already has any double verification prevention roles
                if is_already_verified(member):
                    await interaction.response.send_message("You are already verified! No need to verify again.", ephemeral=True)
                    return

        if self.bot_data.has_pending_request(user.id):
            await interaction.response.send_message("You already have a pending verification request!", ephemeral=True)
            return

        await interaction.response.send_message(f"Sending verification request over API{EMOJI_LOADING}", ephemeral=True)
        await asyncio.sleep(1)

        self.bot_data.add_request(user.id)

        if self.bot_data.auto_accept_enabled:
            await self.auto_accept_request(interaction, user, main_guild)
        else:
            await interaction.edit_original_response(content=f"Request sent over API {EMOJI_CHECKMARK}\nNow wait for the request handlers to respond...")

            request_channel = get_channel_global(interaction.client, REQUEST_CHANNEL_ID)
            if request_channel:
                try:
                    embed = discord.Embed(
                        title=f"{EMOJI_LOCKED} New Verification Request",
                        description=f"> *Incoming verification request detected.*\n\n"
                                   f"**User:** {user.mention} (`{user.name}`)\n"
                                   f"**ID:** `{user.id}`\n"
                                   f"**From:** {main_guild.name if main_guild else 'Unknown'}",
                        color=0x2b2d31,
                        timestamp=datetime.now()
                    )
                    embed.set_thumbnail(url=user.display_avatar.url)
                    request_view = RequestHandlerView(self.bot_data, user.id)
                    await request_channel.send(embed=embed, view=request_view)
                except Exception as e:
                    print(f"[ERROR] Error sending request: {e}")

    async def auto_accept_request(self, interaction, user, main_guild):
        if not main_guild:
            try:
                await interaction.edit_original_response(content=f"{EMOJI_XMARK} Error: Guild not found!")
            except:
                pass
            return

        member = main_guild.get_member(user.id)
        if not member:
            try:
                await interaction.edit_original_response(content=f"{EMOJI_XMARK} Error: You are not in the server!")
            except:
                pass
            return

        # Double check verification prevention
        if is_already_verified(member):
            try:
                await interaction.edit_original_response(content=f"{EMOJI_CHECKMARK} You are already verified!")
            except:
                pass
            return

        self.bot_data.update_request(user.id, 'accepted')
        bot_member = main_guild.get_member(interaction.client.user.id)

        # Step 1: Add roles from ROLES_ADD_ON_VERIFY
        for role_id in ROLES_ADD_ON_VERIFY:
            role = main_guild.get_role(role_id)
            if role and role not in member.roles:
                try:
                    if bot_member and bot_member.top_role <= role:
                        print(f"[WARNING] Role {role.name} (ID: {role_id}) is above bot's highest role")
                        continue
                    await member.add_roles(role)
                    print(f"[AUTO-ACCEPT] Added role {role.name} to {member.name}")
                except discord.Forbidden:
                    print(f"[WARNING] Missing permissions to add role {role.name}")
                except Exception as e:
                    print(f"[ERROR] Error adding role: {e}")

        # Step 2: Remove roles from ROLE_REMOVE_AFTER_VERIFY
        for role_id in ROLE_REMOVE_AFTER_VERIFY:
            remove_role = main_guild.get_role(role_id)
            if remove_role and remove_role in member.roles:
                try:
                    if bot_member and bot_member.top_role <= remove_role:
                        print(f"[WARNING] Role {remove_role.name} is above bot's highest role")
                    else:
                        await member.remove_roles(remove_role)
                        print(f"[AUTO-ACCEPT] Removed role {remove_role.name} from {member.name}")
                except discord.Forbidden:
                    print(f"[WARNING] Missing permissions to remove role {remove_role.name}")
                except Exception as e:
                    print(f"[ERROR] Error removing role: {e}")

        self.bot_data.mark_verified(member.id)

        try:
            await interaction.edit_original_response(content=f"Request sent over API {EMOJI_CHECKMARK}\n{EMOJI_CHECKMARK} Auto-accepted! Welcome!")
        except:
            pass

        try:
            embed = discord.Embed(
                title=f"{EMOJI_CHECKMARK} Verification Accepted (Auto)",
                description=f"> *Your identity has been verified automatically.*\n\n"
                           f"Welcome to **{main_guild.name}**.\n"
                           f"You now have full access.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            if self.bot_data.auto_uy_enabled:
                embed.add_field(
                    name=f"{EMOJI_WARNING} Note",
                    value=f"If you don't send any messages for {INACTIVITY_TIMEOUT_MINUTES}+ minutes, "
                          f"you will automatically lose your verified roles.",
                    inline=False
                )
            embed.set_footer(text=f"{main_guild.name} • Auto-Verification System • 24/7 Active")
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

        log_channel = get_channel_global(interaction.client, LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title=f"{EMOJI_CHECKMARK} Verification Accepted (Auto)",
                description=f"> *Auto-verification processed successfully.*\n\n"
                           f"**User:** {member.mention} (`{member.name}`)\n"
                           f"**System:** Auto-Accept\n"
                           f"**From:** {main_guild.name}",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            log_embed.set_footer(text=f"{main_guild.name} • Verification Log • 24/7 Active")
            await log_channel.send(embed=log_embed)

        print(f"[AUTO-ACCEPT] Automatically accepted {member.name}")


class RequestHandlerView(View):
    def __init__(self, bot_data, requested_user_id):
        super().__init__(timeout=None)
        self.bot_data = bot_data
        self.requested_user_id = requested_user_id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="handler_accept")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        requested_user, main_guild = get_member_global(interaction.client, self.requested_user_id)

        if not requested_user:
            try:
                await interaction.response.send_message("User not found! They might have left the server.", ephemeral=True)
            except:
                pass
            return

        if not self.bot_data.has_pending_request(self.requested_user_id):
            try:
                await interaction.response.send_message("This request has already been processed!", ephemeral=True)
            except:
                pass
            return

        # Check if user is already verified
        if is_already_verified(requested_user):
            try:
                await interaction.response.send_message("This user is already verified!", ephemeral=True)
            except:
                pass
            return

        self.bot_data.update_request(self.requested_user_id, 'accepted')
        bot_member = main_guild.get_member(interaction.client.user.id)

        # Step 1: Add roles from ROLES_ADD_ON_VERIFY
        for role_id in ROLES_ADD_ON_VERIFY:
            role = main_guild.get_role(role_id)
            if role and role not in requested_user.roles:
                try:
                    if bot_member and bot_member.top_role <= role:
                        print(f"[WARNING] Role {role.name} (ID: {role_id}) is above bot's highest role")
                        continue
                    await requested_user.add_roles(role)
                    print(f"[ACCEPT] Added role {role.name} to {requested_user.name}")
                except discord.Forbidden:
                    print(f"[WARNING] Missing permissions to add role {role.name}")
                except Exception as e:
                    print(f"[ERROR] Error adding role: {e}")

        # Step 2: Remove roles from ROLE_REMOVE_AFTER_VERIFY
        for role_id in ROLE_REMOVE_AFTER_VERIFY:
            remove_role = main_guild.get_role(role_id)
            if remove_role and remove_role in requested_user.roles:
                try:
                    if bot_member and bot_member.top_role <= remove_role:
                        print(f"[WARNING] Role {remove_role.name} is above bot's highest role")
                    else:
                        await requested_user.remove_roles(remove_role)
                        print(f"[ACCEPT] Removed role {remove_role.name} from {requested_user.name}")
                except discord.Forbidden:
                    print(f"[WARNING] Missing permissions to remove role {remove_role.name}")
                except Exception as e:
                    print(f"[ERROR] Error removing role: {e}")

        self.bot_data.mark_verified(requested_user.id)

        try:
            embed = discord.Embed(
                title=f"{EMOJI_CHECKMARK} Verification Accepted",
                description=f"> *Your identity has been verified.*\n\n"
                           f"Welcome to **{main_guild.name}**.\n"
                           f"Approved by {interaction.user.mention}.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            if self.bot_data.auto_uy_enabled:
                embed.add_field(
                    name=f"{EMOJI_WARNING} Note",
                    value=f"If you don't send any messages for {INACTIVITY_TIMEOUT_MINUTES}+ minutes, "
                          f"you will automatically lose your verified roles.",
                    inline=False
                )
            embed.set_footer(text=f"{main_guild.name} • Verification System • 24/7 Active")
            await requested_user.send(embed=embed)
        except discord.Forbidden:
            pass

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.description += f"\n\n{EMOJI_CHECKMARK} **Accepted by:** {interaction.user.mention}\n**From:** {main_guild.name}"
        await interaction.message.edit(embed=embed, view=None)

        try:
            await interaction.response.send_message(f"Verification for {requested_user.mention} has been accepted!", ephemeral=True)
        except:
            pass

        log_channel = get_channel_global(interaction.client, LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title=f"{EMOJI_CHECKMARK} Verification Accepted",
                description=f"> *Manual verification approved.*\n\n"
                           f"**User:** {requested_user.mention} (`{requested_user.name}`)\n"
                           f"**By:** {interaction.user.mention} (`{interaction.user.name}`)\n"
                           f"**From:** {main_guild.name}",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            log_embed.set_footer(text=f"{main_guild.name} • Verification Log • 24/7 Active")
            await log_channel.send(embed=log_embed)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, custom_id="handler_decline")
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        requested_user, main_guild = get_member_global(interaction.client, self.requested_user_id)

        if not requested_user:
            try:
                await interaction.response.send_message("User not found!", ephemeral=True)
            except:
                pass
            return

        if not self.bot_data.has_pending_request(self.requested_user_id):
            try:
                await interaction.response.send_message("This request has already been processed!", ephemeral=True)
            except:
                pass
            return

        self.bot_data.update_request(self.requested_user_id, 'declined')

        try:
            embed = discord.Embed(
                title=f"{EMOJI_XMARK} Verification Declined",
                description=f"> *Your verification request was not approved.*\n\n"
                           f"Declined by {interaction.user.mention}.\n"
                           f"Contact staff if you believe this is an error.",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"{main_guild.name} • Verification System • 24/7 Active")
            await requested_user.send(embed=embed)
        except discord.Forbidden:
            pass

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.description += f"\n\n{EMOJI_XMARK} **Declined by:** {interaction.user.mention}\n**From:** {main_guild.name}"
        await interaction.message.edit(embed=embed, view=None)

        try:
            await interaction.response.send_message(f"Verification for {requested_user.mention} has been declined.", ephemeral=True)
        except:
            pass

        log_channel = get_channel_global(interaction.client, LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title=f"{EMOJI_XMARK} Verification Declined",
                description=f"> *Verification request rejected.*\n\n"
                           f"**User:** {requested_user.mention} (`{requested_user.name}`)\n"
                           f"**By:** {interaction.user.mention} (`{interaction.user.name}`)\n"
                           f"**From:** {main_guild.name}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            log_embed.set_footer(text=f"{main_guild.name} • Verification Log • 24/7 Active")
            await log_channel.send(embed=log_embed)


class EmergencyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    def get_role_counts(self, guild):
        verified_members = set()
        for role_id in DOUBLE_VERIFICATION_PREVENTION_ROLES:
            role = guild.get_role(role_id)
            if role:
                verified_members.update(role.members)

        unverified_members = set()
        for role_id in ROLES_ADD_MANUAL:
            role = guild.get_role(role_id)
            if role:
                unverified_members.update(role.members)

        return len(verified_members), len(unverified_members)

    @discord.ui.button(label="EMS-TAKE", style=discord.ButtonStyle.red, custom_id="emergency_take_button")
    async def emergency_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        main_guild = interaction.client.get_guild(MAIN_GUILD_ID)
        embed = discord.Embed(
            title=f"{EMOJI_WARNING} Emergency Role Take Confirmation",
            description=f"> *Warning: This action is irreversible.*\n\n"
                       f"**From:** {main_guild.name if main_guild else 'Unknown'}\n"
                       "Strip verified roles from **all** members\n"
                       "and assign unverified roles to everyone.\n"
                       "**This confirmation expires in 5 minutes!**",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        confirm_view = EmergencyConfirmView(interaction.guild)
        await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)

    @discord.ui.button(label="VIEW", style=discord.ButtonStyle.blurple, custom_id="emergency_view_button")
    async def view_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        main_guild = interaction.client.get_guild(MAIN_GUILD_ID)
        if not main_guild:
            main_guild = interaction.guild
        verified_count, unverified_count = self.get_role_counts(main_guild)
        embed = discord.Embed(
            title=f"{EMOJI_STATS} Role Statistics",
            description=f"> *Real-time role distribution overview.*\n\n"
                       f"**Verified:** {verified_count} members\n"
                       f"**Unverified:** {unverified_count} members\n"
                       f"**Server:** {main_guild.name}",
            color=0x2b2d31,
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"{main_guild.name} • Statistics • 24/7 Active")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="AUTO-ACCEPT", style=discord.ButtonStyle.green, custom_id="emergency_auto_accept_button")
    async def auto_accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        aa_enabled = interaction.client.bot_data.auto_accept_enabled
        status_text = f"Enabled {EMOJI_CHECKMARK}" if aa_enabled else f"Disabled {EMOJI_XMARK}"
        embed = discord.Embed(
            title=f"{EMOJI_LOCKED} Auto-Accept Configuration",
            description=f"> *Configure automatic request handling.*\n\n"
                       f"**Status:** {status_text}\n"
                       f"Toggle below to enable or disable auto-accept.",
            color=0x2b2d31,
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"{interaction.client.get_guild(MAIN_GUILD_ID).name if interaction.client.get_guild(MAIN_GUILD_ID) else 'Unknown'} • Auto-Accept System • 24/7 Active")
        view = AutoAcceptView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="AUTO-UY", style=discord.ButtonStyle.green, custom_id="emergency_auto_uy_button")
    async def auto_uy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        uy_enabled = interaction.client.bot_data.auto_uy_enabled
        status_text = f"Enabled {EMOJI_CHECKMARK}" if uy_enabled else f"Disabled {EMOJI_XMARK}"
        embed = discord.Embed(
            title=f"{EMOJI_LOCKED} Auto-UY Configuration",
            description=f"> *Configure automatic unverification.*\n\n"
                       f"**Status:** {status_text}\n"
                       f"Inactivity threshold: {INACTIVITY_TIMEOUT_MINUTES}+ min.",
            color=0x2b2d31,
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"{interaction.client.get_guild(MAIN_GUILD_ID).name if interaction.client.get_guild(MAIN_GUILD_ID) else 'Unknown'} • Auto-UY System • 24/7 Active")
        view = AutoUYView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class EmergencyConfirmView(View):
    def __init__(self, guild):
        super().__init__(timeout=300)
        self.guild = guild

    async def on_timeout(self):
        try:
            for item in self.children:
                item.disabled = True
            if hasattr(self, 'message'):
                await self.message.edit(view=self)
        except:
            pass

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.danger, custom_id="emergency_yes_confirm")
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        main_guild = interaction.client.get_guild(MAIN_GUILD_ID)
        if not main_guild:
            await interaction.response.send_message("Main guild not found!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        bot_member = main_guild.get_member(interaction.client.user.id)
        affected_members = 0
        ignored_ids = {str(uid) for uid in ROLES_IGNORE}

        for member in main_guild.members:
            if member.bot or str(member.id) in ignored_ids:
                continue
            try:
                # Remove verified roles (ROLES_REMOVE_MANUAL)
                for role_id in ROLES_REMOVE_MANUAL:
                    role = main_guild.get_role(role_id)
                    if role and role in member.roles:
                        if bot_member and bot_member.top_role <= role:
                            print(f"[WARNING] Role {role.name} (ID: {role.id}) is above bot's highest role")
                        else:
                            await member.remove_roles(role)
                            print(f"[EMS-TAKE] Removed {role.name} from {member.name}")
                
                # Add unverified roles (ROLES_ADD_MANUAL)
                for role_id in ROLES_ADD_MANUAL:
                    role = main_guild.get_role(role_id)
                    if role and role not in member.roles:
                        if bot_member and bot_member.top_role <= role:
                            print(f"[WARNING] Role {role.name} is above bot's highest role")
                        else:
                            await member.add_roles(role)
                            print(f"[EMS-TAKE] Added {role.name} to {member.name}")
                
                affected_members += 1
            except Exception as e:
                print(f"[ERROR] Error processing {member.name}: {e}")
                continue

        embed = discord.Embed(
            title=f"{EMOJI_CHECKMARK} Emergency Role Take Complete",
            description=f"> *Emergency protocol executed successfully.*\n\n"
                       f"Processed **{affected_members}** members from **{main_guild.name}**.\n"
                       f"Verified roles removed and unverified roles assigned.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"{main_guild.name} • Emergency Protocol • Initiated by {interaction.user.name}")

        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(embed=embed, view=self)

        log_channel = get_channel_global(interaction.client, LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title=f"{EMOJI_CLIPBOARD} Emergency Role Take Log",
                description=f"> *Emergency protocol has been logged.*\n\n"
                           f"**Initiated by:** {interaction.user.mention} (`{interaction.user.name}`)\n"
                           f"**From:** {main_guild.name}\n"
                           f"**Members affected:** {affected_members}",
                color=0x2b2d31,
                timestamp=datetime.now()
            )
            log_embed.set_footer(text=f"{main_guild.name} • EMS Log • 24/7 Active")
            await log_channel.send(embed=log_embed)

    @discord.ui.button(label="No", style=discord.ButtonStyle.grey, custom_id="emergency_no_confirm")
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        main_guild = interaction.client.get_guild(MAIN_GUILD_ID)
        embed = discord.Embed(
            title=f"{EMOJI_XMARK} Emergency Role Take Cancelled",
            description=f"> *Emergency protocol aborted.*\n\n"
                       f"No changes were made to **{main_guild.name if main_guild else 'Unknown'}**.",
            color=0x2b2d31,
            timestamp=datetime.now()
        )
        for item in self.children:
            item.disabled = True
        await interaction.edit_original_response(embed=embed, view=self)


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.bot_data = BotData()

    async def setup_hook(self):
        await fetch_emoji_ids()
        self.add_view(VerifyView(self.bot_data))
        self.add_view(EmergencyView())
        self.check_inactivity.start()

    async def on_ready(self):
        print(f'[BOT] Ready: {self.user}')
        
        # Check main guild
        main_guild = self.get_guild(MAIN_GUILD_ID)
        if main_guild:
            print(f'[BOT] Main guild: {main_guild.name} ({len(main_guild.members)} members)')
            if self.bot_data.auto_uy_enabled:
                for role_id in DOUBLE_VERIFICATION_PREVENTION_ROLES:
                    prevention_role = main_guild.get_role(role_id)
                    if prevention_role:
                        for member in prevention_role.members:
                            if not member.bot and not is_ignored_user(member.id):
                                self.bot_data.update_last_message(member.id)
                                print(f'[INIT] Set last message time for {member.name} to now')
        
        # Check remote guild
        remote_guild = self.get_guild(REMOTE_GUILD_ID)
        if remote_guild:
            print(f'[BOT] Remote guild: {remote_guild.name} ({len(remote_guild.members)} members)')
        
        await self.update_existing_embeds()

    async def on_message(self, message):
        if message.guild and message.guild.id == MAIN_GUILD_ID and not message.author.bot:
            if not is_ignored_user(message.author.id) and self.bot_data.auto_uy_enabled:
                self.bot_data.update_last_message(message.author.id)

    @tasks.loop(minutes=1)
    async def check_inactivity(self):
        if not self.bot_data.auto_uy_enabled:
            return

        main_guild = self.get_guild(MAIN_GUILD_ID)
        if not main_guild:
            return

        bot_member = main_guild.get_member(self.user.id)
        if not bot_member:
            return

        inactive_users = self.bot_data.get_inactive_users(main_guild, INACTIVITY_TIMEOUT_MINUTES)

        if not inactive_users:
            return

        for member in inactive_users:
            # Remove verified roles (ROLES_REMOVE_AUTO)
            for role_id in ROLES_REMOVE_AUTO:
                role = main_guild.get_role(role_id)
                if role and role in member.roles:
                    try:
                        if bot_member.top_role <= role:
                            print(f"[WARNING] Cannot remove {role.name} - above bot's role")
                        else:
                            await member.remove_roles(role)
                            print(f"[INACTIVITY] Removed {role.name} from {member.name}")
                    except Exception as e:
                        print(f"[ERROR] Failed to remove {role.name}: {e}")

            # Add unverified roles (ROLES_ADD_AUTO)
            for role_id in ROLES_ADD_AUTO:
                unverified_role = main_guild.get_role(role_id)
                if unverified_role and unverified_role not in member.roles:
                    try:
                        if bot_member.top_role <= unverified_role:
                            print(f"[WARNING] Cannot add {unverified_role.name} - above bot's role")
                        else:
                            await member.add_roles(unverified_role)
                            print(f"[INACTIVITY] Added {unverified_role.name} to {member.name}")
                    except Exception as e:
                        print(f"[ERROR] Failed to add {unverified_role.name}: {e}")

            try:
                dm_embed = discord.Embed(
                    title=f"{EMOJI_WARNING} Inactivity Notice",
                    description=f"> *Inactivity threshold exceeded.*\n\n"
                               f"You have been unverified from **{main_guild.name}**\n"
                               f"due to {INACTIVITY_TIMEOUT_MINUTES}+ minutes of inactivity.\n"
                               f"Re-verify to regain access.",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                dm_embed.set_footer(text=f"{main_guild.name} • Auto-Moderation • 24/7 Active")
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass

            uid = str(member.id)
            if uid in self.bot_data.verified_since:
                del self.bot_data.verified_since[uid]
            if uid in self.bot_data.last_message_time:
                del self.bot_data.last_message_time[uid]
            self.bot_data.save_data()

            log_channel = get_channel_global(self, LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title=f"{EMOJI_CLOCK} Inactivity EMS Take",
                    description=f"> *Automated inactivity enforcement.*\n\n"
                               f"**User:** {member.mention} (`{member.name}`)\n"
                               f"**From:** {main_guild.name}\n"
                               f"**Reason:** {INACTIVITY_TIMEOUT_MINUTES}+ min inactive",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                log_embed.set_footer(text=f"{main_guild.name} • Auto-EMS Log • 24/7 Active")
                await log_channel.send(embed=log_embed)

            await asyncio.sleep(0.5)

    @check_inactivity.before_loop
    async def before_check_inactivity(self):
        await self.wait_until_ready()

    async def update_existing_embeds(self):
        main_guild = self.get_guild(MAIN_GUILD_ID)
        guild_name = main_guild.name if main_guild else "Unknown"

        # Update verify channel in main guild
        verify_channel = get_channel_global(self, VERIFY_CHANNEL_ID)
        if verify_channel:
            BANNER_URL = "https://cdn.discordapp.com/attachments/1512089599227203615/1512090622855614696/SGM-Company-final.png?ex=6a22d3a1&is=6a218221&hm=68510c7916196fe0304cea912bb5204c9ce41ccb1005742bffa287858c93d104&"
            found = False
            async for msg in verify_channel.history(limit=50):
                if msg.author == self.user and msg.embeds:
                    embed = discord.Embed(
                        title=f"{EMOJI_LOCKED} Welcome to **{guild_name}**",
                        description=f"> *Secure your access. Prove you're human.*\n\n"
                                   f"Click the button below to begin verification.\n"
                                   f"One request at a time.",
                        color=0x2b2d31,
                        timestamp=datetime.now()
                    )
                    embed.set_image(url=BANNER_URL)
                    embed.set_footer(text=f"{guild_name} • Verification Gateway • 24/7 Active")
                    await msg.edit(embed=embed, view=VerifyView(self.bot_data))
                    found = True
                    break
            if not found:
                embed = discord.Embed(
                    title=f"{EMOJI_LOCKED} Welcome to **{guild_name}**",
                    description=f"> *Secure your access. Prove you're human.*\n\n"
                               f"Click the button below to begin verification.\n"
                               f"One request at a time.\n"
                               f"Already verified? You cannot submit again.",
                    color=0x2b2d31,
                    timestamp=datetime.now()
                )
                embed.set_image(url=BANNER_URL)
                embed.set_footer(text=f"{guild_name} • Verification Gateway • 24/7 Active")
                await verify_channel.send(embed=embed, view=VerifyView(self.bot_data))

        # Update request channel (typically in remote guild)
        request_channel = get_channel_global(self, REQUEST_CHANNEL_ID)
        if request_channel:
            found = False
            async for msg in request_channel.history(limit=50):
                if msg.author == self.user and msg.embeds and not msg.components:
                    embed = discord.Embed(
                        title=f"{EMOJI_LOCKED} Request Handler System",
                        description=f"> *Monitoring for incoming verification requests.*\n\n"
                                   f"**Status:** Online {EMOJI_CHECKMARK}\n"
                                   f"New requests appear below with Accept/Decline.",
                        color=0x2b2d31,
                        timestamp=datetime.now()
                    )
                    embed.set_footer(text=f"{guild_name} • Request Handler • 24/7 Active")
                    await msg.edit(embed=embed)
                    found = True
                    break
            if not found:
                embed = discord.Embed(
                    title=f"{EMOJI_LOCKED} Request Handler System",
                    description=f"> *Monitoring for incoming verification requests.*\n\n"
                               f"**Status:** Online {EMOJI_CHECKMARK}\n"
                               f"New requests appear below with Accept/Decline.",
                    color=0x2b2d31,
                    timestamp=datetime.now()
                )
                embed.set_footer(text=f"{guild_name} • Request Handler • 24/7 Active")
                await request_channel.send(embed=embed)

        # Update control panel channel (typically in remote guild)
        control_panel_channel = get_channel_global(self, CONTROL_PANEL_CHANNEL_ID)
        if control_panel_channel:
            auto_ems_line = f"**Auto-EMS:** {INACTIVITY_TIMEOUT_MINUTES}+ min inactive = auto removal\n" if self.bot_data.auto_uy_enabled else ""
            found = False
            async for msg in control_panel_channel.history(limit=50):
                if msg.author == self.user and msg.embeds:
                    embed = discord.Embed(
                        title=f"{EMOJI_SIREN} Control Panel System",
                        description=f"> *Centralized server control interface.*\n\n"
                                   "**EMS-TAKE** Emergency striping  •  **VIEW** Statistics\n"
                                   "**AUTO-ACCEPT** Auto verify  •  **AUTO-UY** Auto unverify\n\n"
                                   f"{auto_ems_line}"
                                   "**Use with caution!**",
                        color=0x2b2d31,
                        timestamp=datetime.now()
                    )
                    embed.set_footer(text=f"{guild_name} • Control Panel • 24/7 Active")
                    await msg.edit(embed=embed, view=EmergencyView())
                    found = True
                    break
            if not found:
                embed = discord.Embed(
                    title=f"{EMOJI_SIREN} Control Panel System",
                    description=f"> *Centralized server control interface.*\n\n"
                               "**EMS-TAKE** Emergency striping  •  **VIEW** Statistics\n"
                               "**AUTO-ACCEPT** Auto verify  •  **AUTO-UY** Auto unverify\n\n"
                               f"{auto_ems_line}"
                               "**Use with caution!**",
                    color=0x2b2d31,
                    timestamp=datetime.now()
                )
                embed.set_footer(text=f"{guild_name} • Control Panel • 24/7 Active")
                await control_panel_channel.send(embed=embed, view=EmergencyView())


bot = MyBot()

if __name__ == "__main__":
    bot.run(TOKEN)