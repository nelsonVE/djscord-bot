const {execute} = require('./actions/execute')

function executeAction(message, prefix, serverQueue, queue) {
    const text = message.content
    console.log(text)

    if(text.startsWith(`${prefix}play`))
        execute(message, serverQueue, queue)

    if(text.startsWith(`${prefix}skip`))
        skip(text, queue)

    if(text.startsWith(`${prefix}stop`))
        stop(text, queue)

}

module.exports = {executeAction}