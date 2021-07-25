const {prepareListeners} = require('./listeners')

const Discord = require('discord.js')
const {prefix, token} = require('./config.json')

const client = new Discord.Client()
client.login(token)

prepareListeners(client, prefix)