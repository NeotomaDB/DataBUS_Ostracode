SELECT ts.insertcollectionunit(_handle := %(handle)s,
                                       _collunitname := %(collname)s,
                                       _siteid := %(siteid)s, 
                                       _colltypeid := %(colltypeid)s,
                                       _depenvtid := %(depenvtid)s,
                                       _colldate := %(newdate)s,
                                       _location := %(location)s,
                                       _gpslatitude := %(ns)s, 
                                       _gpslongitude := %(ew)s)