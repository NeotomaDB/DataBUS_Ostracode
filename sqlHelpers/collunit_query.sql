SELECT ts.insertcollectionunit(_handle := %(handle)s,
                               _siteid := %(siteid)s,
                               _colltypeid := %(colltypeid)s,
                               _depenvtid := %(depenvtid)s,
                               _collunitname := %(collunitname)s,
                               _colldate := %(colldate)s,
                               _colldevice := %(colldevice)s,
                               _gpslatitude := %(ns)s, 
                               _gpslongitude := %(ew)s,
                               _gpserror := %(gpserror)s,
                               _waterdepth := %(waterdepth)s,
                               _substrateid := %(substrateid)s,
                               _slopeaspect := %(slopeaspect)s,
                               _slopeangle := %(slopeangle)s,
                               _location := %(location)s,
                               _notes := %(notes)s)