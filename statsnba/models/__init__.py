from mongoengine import connect
import statsnba

connect(statsnba.config['mongodb']['database'])
