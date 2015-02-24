dataSource {
    pooled = true
    driverClassName = "com.mysql.jdbc.Driver"
    username = "sa"
    password = ""
}
hibernate {
    cache.use_second_level_cache = true
    cache.use_query_cache = false
    cache.region.factory_class = 'net.sf.ehcache.hibernate.EhCacheRegionFactory'
}
// environment specific settings
environments {
    production {
    	//example = "true" 
        SERVICE.CDN.ENABLED = "SERVICECDNENABLED"
    	//example = "/api/contents/*"
    	cors.url.pattern = 'MCRAPICONTENTMANAGEMENTPATTERN'
    	//example = "http://localhost:8080"
        cors.allow.origin.regex = 'http://DSSCMSSERVER:80'
		//example = "./files/"
		MCRAPI.storageDirectory = "MCRAPISTORAGEDIRECTORY"
		//example = "http://localhost"
        MCRAPI.storageServerUrl = "MCRAPISTORAGESERVERURL"
		//example = "8081"
        MCRAPI.storageServerPort = "MCRAPISTORAGESERVERPORT"
		//example = "/api/contents"
        MCRAPI.contentManagementUrl = "MCRAPICONTENTMANAGEMENTURL"
	
		//example = "localhost"
        DSS.MCRAPI.DBServerUrl = "DSSMCRAPIDBSERVERURL"
		//example = "mcrapi"
        DSS.MCRAPI.DBName = "DSSMCRAPIDBNAME"
		//example = "root"
        DSS.MCRAPI.DBUsername = "DSSMCRAPIDBUSERNAME"
		//example = ""
        DSS.MCRAPI.DBPassword = "DSSMCRAPIDBPASSWORD"
		
        dataSource {
            dbCreate = "update" // one of 'create', 'create-drop', 'update', 'validate', ''
            url = "jdbc:mysql://" + DSS.MCRAPI.DBServerUrl + "/" + DSS.MCRAPI.DBName + "?useUnicode=yes&characterEncoding=UTF-8"
            // Credentials
            username = DSS.MCRAPI.DBUsername
            password = DSS.MCRAPI.DBPassword
        }
    }
}
