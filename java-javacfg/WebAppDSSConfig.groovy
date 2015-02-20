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
		//example = "http://localhost"
		DSS.MCRAPI.url = "DSSMCRAPIURL"
                //example = "false"
        SERVICE.CDN.ENABLED = "SERVICECDNENABLED"
                //example = "http://localhost"
        SERVICE.CDN.ENABLED = "DSSMCRAPIURL"
		//example = "8081"
        DSS.MCRAPI.port = "DSSMCRAPIPORT"
		//example = "sysadmin"
        DSS.MCRAPI.superAdmin = "DSSMCRAPISUPERADMINUSER"
		//example = "sysadmin2014"
        DSS.MCRAPI.superAdminPassword = "DSSMCRAPISUPERADMINPASSWORD"
		//example = "/api/authentications/login"
        DSS.MCRAPI.loginUrl = "DSSMCRAPILOGINURL"
		//example = "/api/contents"
        DSS.MCRAPI.contentManagementUrl = "DSSMCRAPICONTENTMANAGEMENTURL"
		//example = "/api/users"
        DSS.MCRAPI.userManagementUrl = "DSSMCRAPIUSERMANAGEMENTURL"
                // example = "http://172.16.19.157:8088/mockIdentityProviderServiceImplPortBinding"
        DSS.OPENAM.endPoint = "DSSOPENAMENDPOINT"
		
		//example = "localhost"
		DSS.CS.DBServerUrl = "DSSCSDBSERVERURL"
		//example = "webapp"
        DSS.CS.DBName = "DSSCSDBNAME"
		//example = "root"
        DSS.CS.DBUsername = "DSSCSDBUSERNAME"
		//example = ""
        DSS.CS.DBPassword = "DSSCSDBPASSWORD"
		
        dataSource {
            dbCreate = "update" // one of 'create', 'create-drop', 'update', 'validate', ''
            url = "jdbc:mysql://" + DSS.CS.DBServerUrl + "/" + DSS.CS.DBName + "?useUnicode=yes&characterEncoding=UTF-8"
            // Credentials
            username = DSS.CS.DBUsername
            password = DSS.CS.DBPassword
        }
    }
}

