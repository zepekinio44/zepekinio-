#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Boutique Telegram - Paiement en espèces
Installez: pip install python-telegram-bot==20.7
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

BOT_TOKEN = "8638520685:AAHuZ5qhIfkfih4XkwrNQyMl7VrVsUZFDMk"
ADMIN_CHAT_ID = 8598677918
CHANNEL_USERNAME = "@votre_canal"

PRODUCTS = [
    {"id": 1, "name": "Produit 1", "description": "Description du produit 1", "price": 150, "currency": "DZD", "available": True},
    {"id": 2, "name": "Produit 2", "description": "Description du produit 2", "price": 300, "currency": "DZD", "available": True},
    {"id": 3, "name": "Produit 3", "description": "Description du produit 3", "price": 500, "currency": "DZD", "available": True},
]

CHOOSING_PRODUCT, ENTERING_NAME, ENTERING_PHONE, ENTERING_ADDRESS, CONFIRMING = range(5)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

user_carts = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🛍️ Voir les produits", callback_data="show_products")],
        [InlineKeyboardButton("🛒 Mon panier", callback_data="view_cart")],
        [InlineKeyboardButton("📞 Nous contacter", callback_data="contact")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"👋 Bienvenue *{user.first_name}* !\n\n"
        "🏪 Bienvenue dans notre boutique en ligne.\n"
        "Choisissez une option ci-dessous :",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = []
    for p in PRODUCTS:
        status = "✅" if p["available"] else "❌"
        keyboard.append([InlineKeyboardButton(f"{status} {p['name']} - {p['price']} {p['currency']}", callback_data=f"product_{p['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="back_home")])
    await query.edit_message_text("🛍️ *Nos Produits :*\n\nCliquez sur un produit pour voir les détails.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[1])
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        await query.edit_message_text("❌ Produit introuvable.")
        return
    availability = "✅ Disponible" if product["available"] else "❌ Indisponible"
    keyboard = []
    if product["available"]:
        keyboard.append([InlineKeyboardButton("🛒 Commander maintenant", callback_data=f"order_{product_id}")])
    keyboard.append([InlineKeyboardButton("🔙 Retour aux produits", callback_data="show_products")])
    await query.edit_message_text(
        f"📦 *{product['name']}*\n\n📝 {product['description']}\n\n💰 Prix : *{product['price']} {product['currency']}*\n📊 Statut : {availability}\n\n💵 Paiement : En espèces à la livraison",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split("_")[1])
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    user_id = query.from_user.id
    user_carts[user_id] = {"product": product}
    await query.edit_message_text(
        f"🛒 Commande : *{product['name']}*\n💰 Prix : {product['price']} {product['currency']}\n\n📝 *Étape 1/3* - Veuillez entrer votre *nom complet* :",
        parse_mode="Markdown")
    return ENTERING_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_carts[user_id]["name"] = update.message.text
    await update.message.reply_text("📱 *Étape 2/3* - Entrez votre *numéro de téléphone* :", parse_mode="Markdown")
    return ENTERING_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_carts[user_id]["phone"] = update.message.text
    await update.message.reply_text("📍 *Étape 3/3* - Entrez votre *adresse de livraison complète* :\n\n_(Wilaya, Commune, Rue, N° appartement...)_", parse_mode="Markdown")
    return ENTERING_ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_carts[user_id]["address"] = update.message.text
    cart = user_carts[user_id]
    product = cart["product"]
    keyboard = [
        [InlineKeyboardButton("✅ Confirmer la commande", callback_data="confirm_order")],
        [InlineKeyboardButton("❌ Annuler", callback_data="cancel_order")],
    ]
    await update.message.reply_text(
        f"📋 *Récapitulatif de votre commande :*\n\n📦 Produit : *{product['name']}*\n💰 Prix : *{product['price']} {product['currency']}*\n👤 Nom : {cart['name']}\n📱 Téléphone : {cart['phone']}\n📍 Adresse : {cart['address']}\n\n💵 Paiement : *En espèces à la livraison*\n\nConfirmez-vous votre commande ?",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRMING

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    cart = user_carts.get(user_id, {})
    product = cart.get("product", {})
    user = query.from_user
    await query.edit_message_text("✅ *Commande confirmée !*\n\nMerci pour votre commande 🎉\nNotre équipe vous contactera bientôt pour la livraison.\n\n💵 Paiement en espèces à la livraison.", parse_mode="Markdown")
    admin_message = (
        "🔔 *NOUVELLE COMMANDE !*\n━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Produit :* {product.get('name', 'N/A')}\n💰 *Prix :* {product.get('price', 'N/A')} {product.get('currency', '')}\n━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Nom :* {cart.get('name', 'N/A')}\n📱 *Téléphone :* {cart.get('phone', 'N/A')}\n📍 *Adresse :* {cart.get('address', 'N/A')}\n━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 *Telegram ID :* {user_id}\n👤 *Username :* @{user.username or 'N/A'}\n━━━━━━━━━━━━━━━━━━━━\n💵 *Paiement :* En espèces à la livraison"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Erreur envoi admin: {e}")
    if user_id in user_carts:
        del user_carts[user_id]
    return ConversationHandler.END

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id in user_carts:
        del user_carts[user_id]
    keyboard = [[InlineKeyboardButton("🏠 Accueil", callback_data="back_home")]]
    await query.edit_message_text("❌ Commande annulée.\nRevenez quand vous voulez !", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="back_home")]]
    await query.edit_message_text(
        f"📞 *Contactez-nous :*\n\n📱 WhatsApp / Tél : +213 XXX XXX XXX\n📢 Canal : {CHANNEL_USERNAME}\n\n⏰ Disponibles de 8h à 22h",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def back_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🛍️ Voir les produits", callback_data="show_products")],
        [InlineKeyboardButton("📞 Nous contacter", callback_data="contact")],
    ]
    await query.edit_message_text("🏪 *Menu Principal*\n\nQue souhaitez-vous faire ?", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def cancel_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_carts:
        del user_carts[user_id]
    await update.message.reply_text("❌ Commande annulée. Tapez /start pour recommencer.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_order, pattern="^order_")],
        states={
            ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            ENTERING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ENTERING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            CONFIRMING: [
                CallbackQueryHandler(confirm_order, pattern="^confirm_order$"),
                CallbackQueryHandler(cancel_order, pattern="^cancel_order$"),
            ],
        },
        fallbacks=[CommandHandler("annuler", cancel_text)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(show_products, pattern="^show_products$"))
    app.add_handler(CallbackQueryHandler(product_detail, pattern="^product_"))
    app.add_handler(CallbackQueryHandler(contact, pattern="^contact$"))
    app.add_handler(CallbackQueryHandler(back_home, pattern="^back_home$"))
    print("🤖 Bot démarré ! Appuyez sur Ctrl+C pour arrêter.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

