function share(url, title='', text='') {
    if (navigator.share) {
        navigator.share({
            title: 'Chalkline | ' + title,
            text: text,
            url: url
        })
        .then(() => console.log('Link shared'))
        .catch((error) => console.log('Error: could not share'))
    }
}

function copy(url) {
    navigator.clipboard.writeText(url)
    alert('Copied link!')
}
