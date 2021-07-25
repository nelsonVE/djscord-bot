const {play} = require('./actions/play')

async function queueBuilder(queue, message, song, voiceChannel) {
    const queueContruct = {
        textChannel: message.channel,
        voiceChannel: voiceChannel,
        connection: null,
        songs: [],
        volume: 5,
        playing: true,
    };
    
    queueContruct.songs.push(song);
    queue.set(message.guild.id, queueContruct);
    
    try {
        var connection = await voiceChannel.join();
        queueContruct.connection = connection;
        play(message.guild, queueContruct.songs[0], queue);
    } catch (err) {
        console.log(err);
        queue.delete(message.guild.id);
        return message.channel.send(err);
    }
}

module.exports = {queueBuilder}