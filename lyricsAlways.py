import overlay
import getSongInfoFromSpotify as spotify
import getLyricsFromGenius as genius

from PyQt5.QtWidgets import (
        QApplication,
        QPushButton,
        )
#  from PyQt5.QtCore import Qt  # imported for color

import sys


class User():
    def __init__(self, username, scope, credentials_dict):
        self.username = username
        self.scope = scope
        self.credentials_dict = credentials_dict

        self.token = self.requestToken()

    def getUsername(self):
        return self.username

    def getScope(self):
        return self.scope

    def getCredentialsDict(self):
        return self.credentials_dict

    def requestToken(self):
        token = spotify.get_user_token(
                    self.username,
                    self.scope,
                    self.credentials_dict,
                )
        return token

    def getToken(self):
        return self.token


def getInitialPositionCoordinates(app):
    screen = app.primaryScreen()
    rect = screen.availableGeometry()
    x = 0
    y = int(rect.height() / 5.0)
    width = 200
    height = 3 * int(rect.height() / 5.0)
    return [x, y, width, height]


def checkResponseStatus(response_json):
    status = response_json["meta"]["status"]
    return status


def getSongFromSpotify(user):
    unparsed_playback_info_json = spotify.get_current_playback_info_json(
            user.token
    )
    current_playback_obj = spotify.load_json_into_object(
            unparsed_playback_info_json
    )
    song_title = spotify.getSongTitleFromPlaybackObj(current_playback_obj)
    song_artist = spotify.getSongArtistFromPlaybackObj(current_playback_obj)
    return song_title, song_artist


def getLyricsForSong(song_title, song_artist):
    search_urls = genius.createSearchGETRequestURLs(song_title, song_artist)
    matching_hit = None
    for url in search_urls:
        response_json = genius.searchGenius(url)
        status = checkResponseStatus(response_json)
        if status != 200:
            error_message = "Failed to get lyrics. Search returned status {}."
            error_message = error_message.format(status)
            return error_message

        matching_hit = genius.findMatchingHitInSearchResults(song_title,
                                                             song_artist,
                                                             response_json)

        if matching_hit is not None:
            print("Successful URL: ", url)
            break

    if matching_hit is None:  # Can't find a song page for this song
        no_lyrics_text = "Cannot find lyrics for current song."
        return no_lyrics_text

    song_path = genius.extractSongPathFromGeniusSearchResult(matching_hit)
    lyrics_page_html = genius.getLyricsPageHTMLFromPath(song_path)
    lyrics = genius.parseLyricsPageHTML(lyrics_page_html)
    lyrics = lyrics.strip()  # Remove beginning and ending newlines
    return lyrics


def update(user, la, app):
    title, artist = getSongFromSpotify(user)
    if la.didSongChange(title, artist):
        la.setCurrentSong(title, artist)
        lyrics = getLyricsForSong(title, artist)
        la.setLyrics(lyrics)
        print("Song updated: ", la.getCurrentSong())
        app.processEvents()
        la._scrollToTop()


def main():
    # get user creds
    spotify.check_args()
    username = spotify.get_username()
    scope = spotify.get_scope()
    credentials_pickle_file = "credentials.p"
    credentials_dict = spotify.load_credentials(credentials_pickle_file)
    user = User(username, scope, credentials_dict)
    #  token = spotify.get_user_token(username, scope, credentials_dict)

    title, artist = getSongFromSpotify(user)
    lyrics = getLyricsForSong(title, artist)

    # make app with lyrics
    app = QApplication(sys.argv)
    initial_coords_and_dimens = getInitialPositionCoordinates(app)
    x, y, w, h = initial_coords_and_dimens

    lyrics_overlay = overlay.LyricsOverlay(title, artist, lyrics)
    lyrics_overlay.setGeometry(x, y, w, h)

    push_button_child = lyrics_overlay.findChild(QPushButton)
    push_button_child.clicked.connect(lambda: update(user,
                                                     lyrics_overlay,
                                                     app))

    # change color of entire window
    #  p = lyrics_overlay.palette()
    #  p.setColor(lyrics_overlay.backgroundRole(), Qt.red)
    #  lyrics_overlay.setPalette(p)

    lyrics_overlay.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
