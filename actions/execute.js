const ytdl = require('ytdl-core')
const {queueBuilder} = require('../queueBuilder')

async function execute(message, serverQueue, queue) {
    const args = message.content.split(" ");
    const voiceChannel = message.member.voice.channel;
    const permissions = voiceChannel.permissionsFor(message.client.user);

    if (!voiceChannel)
        return message.channel.send(
            "You need to be in a voice channel to play music!"
        );

    if (!permissions.has("CONNECT") || !permissions.has("SPEAK"))
        return message.channel.send(
            "I need the permissions to join and speak in your voice channel!"
        );
    
    console.log(args[1])
    const info = await ytdl.getInfo(args[1])
    const song = {
        title: info.videoDetails.title,
        url: info.videoDetails.video_url,
    }

    if(!serverQueue) {
        console.log(info)
        queueBuilder(queue, message, song, voiceChannel)
    } else {
        serverQueue.songs.push(song);
        console.log(serverQueue.songs);
        return message.channel.send(`${song.title} has been added to the queue!`);
    }
}

module.exports = {execute}