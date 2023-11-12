import stripe
import discord
from discord.ext import commands
from discord import app_commands
import json

stripe.api_key = ''

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')
    # Sync commands here if needed
    await bot.tree.sync()

def save_to_json(discord_id, stripe_customer_id):
    try:
        data = {}
        with open("customer_links.json", "r") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                pass

        data[discord_id] = stripe_customer_id

        with open("customer_links.json", "w") as file:
            json.dump(data, file, indent=4)

    except FileNotFoundError:
        with open("customer_links.json", "w") as file:
            json.dump({discord_id: stripe_customer_id}, file, indent=4)

@bot.tree.command(name="newcustomer", description="Create a new Stripe customer")
@app_commands.describe(name="Customer's name", email="Customer's email", discord_user="Discord user to link")
async def newcustomer(interaction: discord.Interaction, name: str, email: str, discord_user: discord.User):
    try:
        # Create a new customer in Stripe
        customer = stripe.Customer.create(name=name, email=email)
        
        # Save the Discord ID and Stripe Customer ID to JSON
        save_to_json(str(discord_user.id), customer.id)

        await interaction.response.send_message(f"New Stripe customer created for {discord_user.mention} with ID: {customer.id}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
 

def get_customer_id_from_json(discord_id):
    try:
        with open("customer_links.json", "r") as file:
            data = json.load(file)
        return data.get(discord_id)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    
def remove_customer_from_json(discord_id):
    try:
        with open("customer_links.json", "r") as file:
            data = json.load(file)

        if discord_id in data:
            del data[discord_id]

            with open("customer_links.json", "w") as file:
                json.dump(data, file, indent=4)
    except (FileNotFoundError, json.JSONDecodeError):
        pass


@bot.tree.command(name="delete", description="Delete a Stripe customer based on Discord user")
@app_commands.describe(discord_user="Discord user whose customer data will be deleted")
async def delete_customer(interaction: discord.Interaction, discord_user: discord.User):
    try:
        customer_id = get_customer_id_from_json(str(discord_user.id))

        if customer_id:
            stripe.Customer.delete(customer_id)
            remove_customer_from_json(str(discord_user.id))

            await interaction.response.send_message(f"Stripe customer for {discord_user.mention} has been deleted and removed from records.", ephemeral=True)
        else:
            await interaction.response.send_message(f"No linked Stripe customer for {discord_user.mention}.", ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)



@bot.tree.command(name="createinvoice", description="Create an invoice for a Discord user")
@app_commands.describe(discord_user="Discord user to invoice", amount="Amount to be invoiced", currency="Currency for the invoice")
async def createinvoice(interaction: discord.Interaction, discord_user: discord.User, amount: int, currency: str = "usd"):
    try:
        customer_id = get_customer_id_from_json(str(discord_user.id))

        if not customer_id:
            await interaction.response.send_message(f"No Stripe customer associated with {discord_user.mention}.", ephemeral=True)
            return

        product = stripe.Product.create(name="Project Inspect", type="service")
        price = stripe.Price.create(
            unit_amount=amount,
            currency=currency,
            product=product.id
        )

        # Create an Invoice with a due date
        invoice = stripe.Invoice.create(
            customer=customer_id,
            pending_invoice_items_behavior='exclude',
            collection_method='send_invoice',
            days_until_due=1,
        )

        stripe.InvoiceItem.create(
            customer=customer_id,
            invoice=invoice.id,
            price_data={
                'currency': currency,
                'unit_amount': amount * 100,
                'tax_behavior': 'exclusive',
                'product': product.id,
            }
        )

        invoice = stripe.Invoice.finalize_invoice(invoice.id)

        custom_hex_color = "b100be"
        custom_color = int(custom_hex_color, 16)
        embed = discord.Embed(
            title="New Invoice Created",
            description=f"Please pay via this link: [Invoice Link]({invoice.hosted_invoice_url})",
            color=discord.Color(custom_color)
        )

        embed.set_footer(text="Stripe Integration", icon_url="YOUR_LOGO_URL_HERE")

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

custom_hex_color = "b100be"
custom_color = int(custom_hex_color, 16)

@bot.tree.command(name="billing", description="Access your Stripe billing information")
async def billing(interaction: discord.Interaction):
        embed = discord.Embed(
            title="Billing",
            description=f"Click here to access your billing information: [Billing Portal]({'Portal Link here'})",
            color=discord.Color(custom_color)
        )
        embed.set_footer(text="Stripe", icon_url="")
        await interaction.user.send(embed=embed)
        await interaction.response.send_message("Your billing information has been sent! Check your DMs", ephemeral=True)




bot.run('')