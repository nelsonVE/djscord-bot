const {executeAction} = require("./actions")

function prepareListeners(client, prefix) {
    const queue = new Map()

    client.once('ready', () => {
        console.log('Ready!');
    });

    client.once('reconnecting', () => {
        console.log('Reconnecting!');
    });

    client.once('disconnect', () => {
        console.log('Disconnect!');
    });

    client.on('message', async message => {
        if(message.author.bot || !message.content.startsWith(prefix))
            return

        const serverQueue = queue.get(message.guild.id)
        executeAction(message, prefix, serverQueue, queue)
    })
}

module.exports = {prepareListeners};