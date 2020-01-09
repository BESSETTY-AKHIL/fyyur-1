#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=True, default=False)
    seeking_description = db.Column(db.String(120),nullable=True )
    shows = db.relationship('Show', backref='Venue',lazy=True)

    def __repr__(self):
        return f'<{self.id} {self.name}>'

    # venue's property
    def upcoming_shows(self):
        current_time = datetime.now()
        all_upcoming_shows = db.session.query(show).filter(Shows.start_time >= current_time)
        venue_upcoming_shows = all_upcoming_shows.filter_by(venue_id=self.id).all()
        upcoming_shows_count = all_upcoming_shows.filter_by(venue_id=self.id).count()
        return {"upcoming_shows": venue_upcoming_shows,
                "upcoming_shows_count": upcoming_shows_count
               }

    # venue's property
    def past_shows(self):
        current_time = datetime.now()
        all_past_shows = db.session.query(show).filter(Shows.start_time < current_time)
        venue_past_shows = all_past_shows.filter_by(venue_id=self.id).all()
        past_shows_count = all_past_shows.filter_by(venue_id=self.id).count()
        return {"past_shows": venue_past_shows,
                "past_shows_count": past_shows_count,
               }


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120), default = False)
    shows = db.relationship('Show', backref='Artist', lazy=True)

    def __repr__(self):
        return f'<{self.id} {self.name}>'

    # artist's property
    def upcoming_shows(self):
        current_time = datetime.now()
        all_upcoming_shows = db.session.query(show).filter(Shows.start_time >= current_time)
        artist_upcoming_shows = all_upcoming_shows.filter_by(artist_id=self.id).all()
        upcoming_shows_count = all_upcoming_shows.filter_by(artist_id=self.id).count()
        return {"upcoming_shows": artis_upcoming_shows,
                "upcoming_shows_count": upcoming_shows_count
               }

    # artist's property
    def past_shows(self):
        current_time = datetime.now()
        all_past_shows = db.session.query(show).filter(Shows.start_time < current_time)
        artist_past_shows = all_past_shows.filter_by(artist_id=self.id).all()
        past_shows_count = artist_past_shows.count()
        return {"past_shows": artist_past_shows,
                "past_shows_count": past_shows_count,
               }

class Show(db.Model):
    __tablename__ = 'show'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey(Venue.id), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(Artist.id), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<artist_id: {self.artist_id} venue_id: {self.venue_id}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  city_state = db.session.query(Venue.state,Venue.city).group_by(Venue.state, Venue.city).all()
  data =[]

  # Add venue to an exisitng city, or a new city
  for v in city_state:
      city_state_venues = {"city":v.city, "state":v.state, "venues":[]}
      venues_of_v = db.session.query(Venue.id,Venue.name).filter_by(city=v.city, state=v.state).all()
      for venue in venues_of_v:
          venue_dict = {}
          venue_dict["id"] = venue[0]
          venue_dict["name"] = venue[1]
          venue_dict["num_upcoming_shows"] = Venue.upcoming_shows
          city_state_venues["venues"].append(venue_dict)
      data.append(city_state_venues)

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form['search_term'].lower()
  venues_query = Venue.query.filter(func.lower(Venue.name).like('%{}%'.format(search_term.lower()))
  ).all()
  response={
    "count": len(venues_query),
    "data": []
  }
  for venue in venues_query:
      response["data"].append(
           {
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": venue.upcoming_shows,
            }
      )
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  #get a given venue
  venue = db.session.query(Venue).filter_by(id=venue_id).first()

  #get all shows for given venue
  shows = Show.query.filter_by(venue_id=venue_id).all()
  #return upcoming shows
  def upcoming_shows():
      upcoming_shows = []
      for show in shows:
          if show.start_time >= datetime.now():
                upcoming_shows.append({
                    "artist_id": show.artist_id,
                    "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
                    "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
                    "start_time": format_datetime(str(show.start_time))
                })
      return upcoming_shows

  #return past shows
  def past_shows():
      past_shows = []
      for show in shows:
          if show.start_time < datetime.now():
                past_shows.append({
                      "artist_id": show.artist_id,
                      "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
                      "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
                      "start_time": format_datetime(str(show.start_time))
                  })
      return past_shows

  #data for given venue
  data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows(),
        "upcoming_shows": upcoming_shows(),
        "past_shows_count": len(past_shows()),
        "upcoming_shows_count": len(upcoming_shows())
  }
  return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
      try:
          new_venue = Venue(**{
            "name":request.form['name'],
            "city": request.form['city'],
            "state": request.form['state'],
            "address": request.form['address'],
            "phone":  request.form['phone'],
            "genres": request.form['genres'],
            "facebook_link": request.form['facebook_link'],
          })
          db.session.add(new_venue)
          db.session.commit()
      # on successful db insert, flash success
          flash('Venue ' + request.form['name'] + ' was successfully listed!')
      except:
          db.session.rollback()
          flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
      finally:
          db.session.close()

      return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
   try:
        venue_name = db.session.query(Venue).filter_by(id=venue_id).first().name
        db.session.query(Venue).filter_by(id=venue_id).delete()
        db.session.commit()
        print(f'{venue_name} was successfully deleted')
   except:
        db.session.rollback()
        print(sys.exc_info())
   finally:
        db.session.close()
   # return jsonify({'success': True})
   return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  all_artists = db.session.query(Artist.id,Artist.name).all()
  data =[]
# Add venue to an exisitng city, or a new city
  for artist in all_artists:
      artist_dict ={}
      artist_dict["id"] = artist[0]
      artist_dict["name"] = artist[1]
      data.append(artist_dict)

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form['search_term'].lower()
  artists_query = Artist.query.filter(func.lower(Artist.name).like('%{}%'.format(search_term.lower()))
  ).all()
  response={
    "count": len(artists_query),
    "data": []
  }
  for artist in artists_query:
      response["data"].append(
           {
                "id": artist.id,
                "name": artist.name,
                "num_upcoming_shows": artist.upcoming_shows,
            }
      )
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  #get a given artis
  artist = db.session.query(Artist).filter_by(id=artist_id).first()

  #get all shows for given artis
  shows = Show.query.filter_by(artist_id=artist_id).all()
  #return upcoming shows
  def upcoming_shows():
      upcoming_shows = []
      for show in shows:
          if show.start_time >= datetime.now():
                upcoming_shows.append({
                    "venue_id": show.venue_id,
                    "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
                    "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
                    "start_time": format_datetime(str(show.start_time))
                })
      return upcoming_shows

  #return past shows
  def past_shows():
      past_shows = []
      for show in shows:
          if show.start_time < datetime.now():
                past_shows.append({
                     "venue_id": show.venue_id,
                     "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
                     "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
                     "start_time": format_datetime(str(show.start_time))
                  })
      return past_shows

  #data for given venue
  data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows(),
        "upcoming_shows": upcoming_shows(),
        "past_shows_count": len(past_shows()),
        "upcoming_shows_count": len(upcoming_shows())
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()

    #get the artist by id
    artist = Artist.query.get(artist_id)

    # populate form with fields from artist with ID <artist_id>
    artist={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }

    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # catch exceptions with try-except block
    try:
        # load data from user input on form submit

        form = ArtistForm(request.form)
        artist = db.session.query(Artist).filter_by(id=artist_id).first()
        artist.name = form.name.data
        artist.image_link = form.image_link.data
        artist.phone = form.phone.data
        artist.state = form.state.data
        artist.city = form.city.data
        artist.facebook_link = form.facebook_link.data
        artist.genres = ",".join(form.genres.data)

        # commit the changes
        db.session.commit()

        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    except:
        # catch all exceptions
        db.session.rollback()
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be updated.')
    finally:
        # always close the session
        db.session.close()

    # return redirect to artist page
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  #get the venue by id
  venue = Venue.query.get(venue_id)

  #load venue data
  venue={
    "id": venue.id,
    "name": venue.name,
    "genres":venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "facebook_link": venue.facebook_link,
    }

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  # catch exceptions with try-except block
    try:
        # load data from user input on form submit

        form = VenueForm(request.form)
        venue = db.session.query(Venue).filter_by(id=venue_id).first()
        venue.name = form.name.data
        venue.genres = ",".join(form.genres.data)
        venue.address = form.address.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.phone = form.phone.data
        venue.facebook_link = form.facebook_link.data


        # commit the changes
        db.session.commit()

        flash('Venue ' + request.form['name'] + ' was successfully updated!')
    except:
        # catch all exceptions
        db.session.rollback()
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be updated.')
    finally:
        # always close the session
        db.session.close()

    # return redirect to venue page
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    new_artist = Artist(**{
      "name":request.form['name'],
      "city": request.form['city'],
      "state": request.form['state'],
      "phone":  request.form['phone'],
      "genres": request.form['genres'],
      "facebook_link": request.form['facebook_link'],
      "image_link": request.form['image_link'],
    })
    db.session.add(new_artist)
    db.session.commit()
  # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
       db.session.rollback()
       flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
       db.session.close()
  return render_template('pages/home.html')

@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
   try:
        artist_name = db.session.query(Artist).filter_by(id=artist_id).first().name
        db.session.query(Artist).filter_by(id=artist_id).delete()
        db.session.commit()
        print(f'{artist_name} was successfully deleted')
   except:
        db.session.rollback()
        print(sys.exc_info())
   finally:
        db.session.close()
   # return jsonify({'success': True})
   return redirect(url_for('artists'))

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  all_shows = db.session.query(Show).all()
  data =[]

  for show in all_shows:
       show_dict ={}
       show_dict["venue_id"] = show.venue_id
       show_dict["venue_name"] = show.Venue.name
       show_dict["artist_id"] = show.artist_id
       show_dict["artist_name"] = show.Artist.name
       show_dict["artist_image_link"] = show.Artist.image_link
       show_dict["start_time"] = show.start_time.strftime("%Y-%m-%d %H:%M:%S")
       data.append(show_dict)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
      new_show = Show(**{
          "artist_id":request.form['artist_id'],
          "venue_id": request.form['venue_id'],
          "start_time": request.form['start_time'],
      })
      db.session.add(new_show)
      db.session.commit()

  # on successful db insert, flash success
      flash('Show was successfully listed!')
  except:
        db.session.rollback()
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
        db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
