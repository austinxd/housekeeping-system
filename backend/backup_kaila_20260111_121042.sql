mysqldump: [Warning] Using a password on the command line interface can be insecure.
Warning: A partial dump from a server that has GTIDs will by default include the GTIDs of all transactions, even those that changed suppressed parts of the database. If you don't want to restore GTIDs, pass --set-gtid-purged=OFF. To make a complete dump, pass --all-databases --triggers --routines --events. 
Warning: A dump from a server that has GTIDs enabled will by default include the GTIDs of all transactions, even those that were executed during its extraction and might not be represented in the dumped data. This might result in an inconsistent data dump. 
In order to ensure a consistent backup of the database, pass --single-transaction or --lock-all-tables or --source-data. 
-- MySQL dump 10.13  Distrib 9.5.0, for macos15 (arm64)
--
-- Host: localhost    Database: kaila
-- ------------------------------------------------------
-- Server version	9.5.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ 'e76ff97c-cc69-11f0-a9e0-fa3c3b728d6d:1-9595';

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=129 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add Bloque Temporal',7,'add_timeblock'),(26,'Can change Bloque Temporal',7,'change_timeblock'),(27,'Can delete Bloque Temporal',7,'delete_timeblock'),(28,'Can view Bloque Temporal',7,'view_timeblock'),(29,'Can add Tipo de Tarea',8,'add_tasktype'),(30,'Can change Tipo de Tarea',8,'change_tasktype'),(31,'Can delete Tipo de Tarea',8,'delete_tasktype'),(32,'Can view Tipo de Tarea',8,'view_tasktype'),(33,'Can add Edificio',9,'add_building'),(34,'Can change Edificio',9,'change_building'),(35,'Can delete Edificio',9,'delete_building'),(36,'Can view Edificio',9,'view_building'),(37,'Can add Zona',10,'add_zone'),(38,'Can change Zona',10,'change_zone'),(39,'Can delete Zona',10,'delete_zone'),(40,'Can view Zona',10,'view_zone'),(41,'Can add Tipo de Habitación',11,'add_roomtype'),(42,'Can change Tipo de Habitación',11,'change_roomtype'),(43,'Can delete Tipo de Habitación',11,'delete_roomtype'),(44,'Can view Tipo de Habitación',11,'view_roomtype'),(45,'Can add Habitación',12,'add_room'),(46,'Can change Habitación',12,'change_room'),(47,'Can delete Habitación',12,'delete_room'),(48,'Can view Habitación',12,'view_room'),(49,'Can add Día de la Semana',13,'add_dayofweek'),(50,'Can change Día de la Semana',13,'change_dayofweek'),(51,'Can delete Día de la Semana',13,'delete_dayofweek'),(52,'Can view Día de la Semana',13,'view_dayofweek'),(53,'Can add Rol',14,'add_role'),(54,'Can change Rol',14,'change_role'),(55,'Can delete Rol',14,'delete_role'),(56,'Can view Rol',14,'view_role'),(57,'Can add Empleado',15,'add_employee'),(58,'Can change Empleado',15,'change_employee'),(59,'Can delete Empleado',15,'delete_employee'),(60,'Can view Empleado',15,'view_employee'),(61,'Can add Equipo/Pareja',16,'add_team'),(62,'Can change Equipo/Pareja',16,'change_team'),(63,'Can delete Equipo/Pareja',16,'delete_team'),(64,'Can view Equipo/Pareja',16,'view_team'),(65,'Can add Indisponibilidad',17,'add_employeeunavailability'),(66,'Can change Indisponibilidad',17,'change_employeeunavailability'),(67,'Can delete Indisponibilidad',17,'delete_employeeunavailability'),(68,'Can view Indisponibilidad',17,'view_employeeunavailability'),(69,'Can add Plantilla de Turno',18,'add_shifttemplate'),(70,'Can change Plantilla de Turno',18,'change_shifttemplate'),(71,'Can delete Plantilla de Turno',18,'delete_shifttemplate'),(72,'Can view Plantilla de Turno',18,'view_shifttemplate'),(73,'Can add Sub-bloque de Turno',19,'add_shiftsubblock'),(74,'Can change Sub-bloque de Turno',19,'change_shiftsubblock'),(75,'Can delete Sub-bloque de Turno',19,'delete_shiftsubblock'),(76,'Can view Sub-bloque de Turno',19,'view_shiftsubblock'),(77,'Can add Estado Diario de Habitación',20,'add_roomdailystate'),(78,'Can change Estado Diario de Habitación',20,'change_roomdailystate'),(79,'Can delete Estado Diario de Habitación',20,'delete_roomdailystate'),(80,'Can view Estado Diario de Habitación',20,'view_roomdailystate'),(81,'Can add Tarea de Habitación',21,'add_roomdailytask'),(82,'Can change Tarea de Habitación',21,'change_roomdailytask'),(83,'Can delete Tarea de Habitación',21,'delete_roomdailytask'),(84,'Can view Tarea de Habitación',21,'view_roomdailytask'),(85,'Can add Log de Importación Protel',22,'add_protelimportlog'),(86,'Can change Log de Importación Protel',22,'change_protelimportlog'),(87,'Can delete Log de Importación Protel',22,'delete_protelimportlog'),(88,'Can view Log de Importación Protel',22,'view_protelimportlog'),(89,'Can add Regla de Tiempo',23,'add_tasktimerule'),(90,'Can change Regla de Tiempo',23,'change_tasktimerule'),(91,'Can delete Regla de Tiempo',23,'delete_tasktimerule'),(92,'Can view Regla de Tiempo',23,'view_tasktimerule'),(93,'Can add Regla de Asignación de Zona',24,'add_zoneassignmentrule'),(94,'Can change Regla de Asignación de Zona',24,'change_zoneassignmentrule'),(95,'Can delete Regla de Asignación de Zona',24,'delete_zoneassignmentrule'),(96,'Can view Regla de Asignación de Zona',24,'view_zoneassignmentrule'),(97,'Can add Regla de Elasticidad',25,'add_elasticityrule'),(98,'Can change Regla de Elasticidad',25,'change_elasticityrule'),(99,'Can delete Regla de Elasticidad',25,'delete_elasticityrule'),(100,'Can view Regla de Elasticidad',25,'view_elasticityrule'),(101,'Can add Parámetro de Planificación',26,'add_planningparameter'),(102,'Can change Parámetro de Planificación',26,'change_planningparameter'),(103,'Can delete Parámetro de Planificación',26,'delete_planningparameter'),(104,'Can view Parámetro de Planificación',26,'view_planningparameter'),(105,'Can add Plan Semanal',27,'add_weekplan'),(106,'Can change Plan Semanal',27,'change_weekplan'),(107,'Can delete Plan Semanal',27,'delete_weekplan'),(108,'Can view Plan Semanal',27,'view_weekplan'),(109,'Can add Asignación de Turno',28,'add_shiftassignment'),(110,'Can change Asignación de Turno',28,'change_shiftassignment'),(111,'Can delete Asignación de Turno',28,'delete_shiftassignment'),(112,'Can view Asignación de Turno',28,'view_shiftassignment'),(113,'Can add Plan Diario',29,'add_dailyplan'),(114,'Can change Plan Diario',29,'change_dailyplan'),(115,'Can delete Plan Diario',29,'delete_dailyplan'),(116,'Can view Plan Diario',29,'view_dailyplan'),(117,'Can add Asignación de Tarea',30,'add_taskassignment'),(118,'Can change Asignación de Tarea',30,'change_taskassignment'),(119,'Can delete Asignación de Tarea',30,'delete_taskassignment'),(120,'Can view Asignación de Tarea',30,'view_taskassignment'),(121,'Can add Resumen de Carga Diaria',31,'add_dailyloadsummary'),(122,'Can change Resumen de Carga Diaria',31,'change_dailyloadsummary'),(123,'Can delete Resumen de Carga Diaria',31,'delete_dailyloadsummary'),(124,'Can view Resumen de Carga Diaria',31,'view_dailyloadsummary'),(125,'Can add Alerta de Planificación',32,'add_planningalert'),(126,'Can change Alerta de Planificación',32,'change_planningalert'),(127,'Can delete Alerta de Planificación',32,'delete_planningalert'),(128,'Can view Alerta de Planificación',32,'view_planningalert');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$600000$aOhVXF1o3aqChuZTVebUco$xI9fomKP9NSSJfdFYzSEEHDizZc1x24lwcb7W03Pbng=','2026-01-08 11:05:08.382261',1,'admin','','','admin@example.com',1,1,'2026-01-08 11:03:29.821346');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_building`
--

DROP TABLE IF EXISTS `core_building`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_building` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(20) NOT NULL,
  `name` varchar(100) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_building`
--

LOCK TABLES `core_building` WRITE;
/*!40000 ALTER TABLE `core_building` DISABLE KEYS */;
INSERT INTO `core_building` VALUES (1,'MAIN','Edificio Principal',1);
/*!40000 ALTER TABLE `core_building` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_dayofweek`
--

DROP TABLE IF EXISTS `core_dayofweek`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_dayofweek` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(3) NOT NULL,
  `name` varchar(20) NOT NULL,
  `iso_weekday` int unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  CONSTRAINT `core_dayofweek_chk_1` CHECK ((`iso_weekday` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_dayofweek`
--

LOCK TABLES `core_dayofweek` WRITE;
/*!40000 ALTER TABLE `core_dayofweek` DISABLE KEYS */;
INSERT INTO `core_dayofweek` VALUES (1,'LUN','Lunes',1),(2,'MAR','Martes',2),(3,'MIE','Miércoles',3),(4,'JUE','Jueves',4),(5,'VIE','Viernes',5),(6,'SAB','Sábado',6),(7,'DOM','Domingo',7);
/*!40000 ALTER TABLE `core_dayofweek` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_room`
--

DROP TABLE IF EXISTS `core_room`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_room` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `number` varchar(20) NOT NULL,
  `order_in_zone` int unsigned NOT NULL,
  `corridor_side` varchar(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `notes` longtext NOT NULL,
  `room_type_id` bigint NOT NULL,
  `zone_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `number` (`number`),
  KEY `core_room_room_type_id_0a8f3c9f_fk_core_roomtype_id` (`room_type_id`),
  KEY `core_room_zone_id_28f1bc75_fk_core_zone_id` (`zone_id`),
  CONSTRAINT `core_room_room_type_id_0a8f3c9f_fk_core_roomtype_id` FOREIGN KEY (`room_type_id`) REFERENCES `core_roomtype` (`id`),
  CONSTRAINT `core_room_zone_id_28f1bc75_fk_core_zone_id` FOREIGN KEY (`zone_id`) REFERENCES `core_zone` (`id`),
  CONSTRAINT `core_room_chk_1` CHECK ((`order_in_zone` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_room`
--

LOCK TABLES `core_room` WRITE;
/*!40000 ALTER TABLE `core_room` DISABLE KEYS */;
INSERT INTO `core_room` VALUES (1,'201',1,'A',1,'',1,1),(2,'202',2,'B',1,'',1,1),(3,'203',3,'A',1,'',1,1),(4,'204',4,'B',1,'',1,1),(5,'205',5,'A',1,'',2,1),(6,'206',6,'B',1,'',1,1),(7,'207',7,'A',1,'',1,1),(8,'301',1,'A',1,'',1,2),(9,'302',2,'B',1,'',2,2),(10,'303',3,'A',1,'',1,2),(11,'304',4,'B',1,'',1,2),(12,'305',5,'A',1,'',1,2),(13,'401',1,'A',1,'',1,3),(14,'402',2,'B',1,'',1,3),(15,'403',3,'A',1,'',1,3),(16,'404',4,'B',1,'',1,3),(17,'405',5,'A',1,'',2,3),(18,'410',6,'A',1,'',3,3),(19,'501',1,'A',1,'',3,4),(20,'502',2,'B',1,'',2,4),(21,'503',3,'A',1,'',1,4);
/*!40000 ALTER TABLE `core_room` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_roomtype`
--

DROP TABLE IF EXISTS `core_roomtype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_roomtype` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(30) NOT NULL,
  `name` varchar(100) NOT NULL,
  `time_multiplier` decimal(3,2) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_roomtype`
--

LOCK TABLES `core_roomtype` WRITE;
/*!40000 ALTER TABLE `core_roomtype` DISABLE KEYS */;
INSERT INTO `core_roomtype` VALUES (1,'STANDARD','Standard',1.00,1),(2,'SUPERIOR','Superior',1.10,1),(3,'SUITE','Suite',1.50,1),(4,'JUNIOR_SUITE','Junior Suite',1.30,1);
/*!40000 ALTER TABLE `core_roomtype` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_tasktype`
--

DROP TABLE IF EXISTS `core_tasktype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_tasktype` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(30) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `base_minutes` int unsigned NOT NULL,
  `priority` int unsigned NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `earliest_start_time` time(6) DEFAULT NULL,
  `latest_end_time` time(6) DEFAULT NULL,
  `persons_required` int unsigned NOT NULL,
  `solo_minutes` int unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  CONSTRAINT `core_tasktype_chk_1` CHECK ((`base_minutes` >= 0)),
  CONSTRAINT `core_tasktype_chk_2` CHECK ((`priority` >= 0)),
  CONSTRAINT `core_tasktype_chk_3` CHECK ((`persons_required` >= 0)),
  CONSTRAINT `core_tasktype_chk_4` CHECK ((`solo_minutes` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_tasktype`
--

LOCK TABLES `core_tasktype` WRITE;
/*!40000 ALTER TABLE `core_tasktype` DISABLE KEYS */;
INSERT INTO `core_tasktype` VALUES (1,'DEPART','Salida','Limpieza completa por checkout',50,10,1,'09:00:00.000000','18:30:00.000000',2,75),(2,'RECOUCH','Recouch','Limpieza de habitación ocupada',20,30,1,'09:00:00.000000','18:30:00.000000',2,30),(5,'COUVERTURE','Couverture','Servicio de cobertura nocturno',15,40,1,'19:00:00.000000','22:30:00.000000',1,15);
/*!40000 ALTER TABLE `core_tasktype` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_tasktype_allowed_blocks`
--

DROP TABLE IF EXISTS `core_tasktype_allowed_blocks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_tasktype_allowed_blocks` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tasktype_id` bigint NOT NULL,
  `timeblock_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `core_tasktype_allowed_bl_tasktype_id_timeblock_id_9f2e4057_uniq` (`tasktype_id`,`timeblock_id`),
  KEY `core_tasktype_allowe_timeblock_id_2a4abc24_fk_core_time` (`timeblock_id`),
  CONSTRAINT `core_tasktype_allowe_tasktype_id_65e7950e_fk_core_task` FOREIGN KEY (`tasktype_id`) REFERENCES `core_tasktype` (`id`),
  CONSTRAINT `core_tasktype_allowe_timeblock_id_2a4abc24_fk_core_time` FOREIGN KEY (`timeblock_id`) REFERENCES `core_timeblock` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_tasktype_allowed_blocks`
--

LOCK TABLES `core_tasktype_allowed_blocks` WRITE;
/*!40000 ALTER TABLE `core_tasktype_allowed_blocks` DISABLE KEYS */;
INSERT INTO `core_tasktype_allowed_blocks` VALUES (1,1,1),(2,2,1),(6,5,2);
/*!40000 ALTER TABLE `core_tasktype_allowed_blocks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_timeblock`
--

DROP TABLE IF EXISTS `core_timeblock`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_timeblock` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(20) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `order` int unsigned NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `end_time` time(6) DEFAULT NULL,
  `start_time` time(6) DEFAULT NULL,
  `helps_other_shift_hours` decimal(3,1) NOT NULL,
  `min_staff` int unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  CONSTRAINT `core_timeblock_chk_1` CHECK ((`order` >= 0)),
  CONSTRAINT `core_timeblock_chk_2` CHECK ((`min_staff` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_timeblock`
--

LOCK TABLES `core_timeblock` WRITE;
/*!40000 ALTER TABLE `core_timeblock` DISABLE KEYS */;
INSERT INTO `core_timeblock` VALUES (1,'DAY','Mañana / Producción','Bloque de limpieza principal (mañana)',1,1,'17:00:00.000000','09:00:00.000000',0.0,2),(2,'EVENING','Tarde + Couverture','Bloque de tarde incluyendo couverture',2,1,'22:30:00.000000','14:00:00.000000',4.5,2),(3,'NIGHT','Noche','Bloque nocturno (équipier de nuit)',3,1,NULL,NULL,0.0,2);
/*!40000 ALTER TABLE `core_timeblock` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `core_zone`
--

DROP TABLE IF EXISTS `core_zone`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `core_zone` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(20) NOT NULL,
  `name` varchar(100) NOT NULL,
  `floor_number` int DEFAULT NULL,
  `priority_order` int unsigned NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `building_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `core_zone_building_id_8f8e84dc_fk_core_building_id` (`building_id`),
  CONSTRAINT `core_zone_building_id_8f8e84dc_fk_core_building_id` FOREIGN KEY (`building_id`) REFERENCES `core_building` (`id`),
  CONSTRAINT `core_zone_chk_1` CHECK ((`priority_order` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `core_zone`
--

LOCK TABLES `core_zone` WRITE;
/*!40000 ALTER TABLE `core_zone` DISABLE KEYS */;
INSERT INTO `core_zone` VALUES (1,'P2','Piso 2',2,1,1,1),(2,'P3','Piso 3',3,2,1,1),(3,'P4','Piso 4',4,3,1,1),(4,'P5','Piso 5',5,4,1,1);
/*!40000 ALTER TABLE `core_zone` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=39 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2026-01-10 03:15:28.206115','7','Ingrid PICAULT (GG)',2,'[{\"changed\": {\"fields\": [\"Last name\"]}}]',15,1),(2,'2026-01-10 03:15:38.828566','7','Ingrid PICAULT (GG)',2,'[]',15,1),(3,'2026-01-10 03:16:15.701515','8','Steffi MONIT (ASST_GG)',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\"]}}]',15,1),(4,'2026-01-10 03:16:32.917437','9','Chertande LEONARD (GOUV_SOIR)',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\"]}}]',15,1),(5,'2026-01-10 03:16:57.517770','10','Dorian PERRIER (FDC)',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\"]}}]',15,1),(6,'2026-01-10 03:17:39.713506','11','Cynthia ROMERO (FDC)',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\"]}}]',15,1),(7,'2026-01-10 03:18:37.017838','13','Gabriela CANADA (FDC)',2,'[{\"changed\": {\"fields\": [\"Last name\"]}}]',15,1),(8,'2026-01-10 03:19:10.335933','15','Inés LE BAIL (VDC)',2,'[{\"changed\": {\"fields\": [\"First name\"]}}]',15,1),(9,'2026-01-10 03:20:16.537195','16','Christopher LADHUIE (VDC)',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\"]}}]',15,1),(10,'2026-01-10 03:22:48.724447','24','Romain LEGEARD (EQUIPIER_NUIT)',2,'[{\"changed\": {\"fields\": [\"Last name\"]}}]',15,1),(11,'2026-01-10 03:23:09.700134','23','Philippe CABANEAU (EQUIPIER_NUIT)',2,'[{\"changed\": {\"fields\": [\"Last name\"]}}]',15,1),(12,'2026-01-10 03:23:44.395202','20','Benjamin GUILLARD (EQUIPIER_JOUR)',2,'[{\"changed\": {\"fields\": [\"Last name\"]}}]',15,1),(13,'2026-01-10 03:24:36.175606','22','Sebastien CAMESCASSE (EQUIPIER_JOUR)',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\"]}}]',15,1),(14,'2026-01-10 03:25:06.646624','12','Marion VIDAL (FDC)',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\"]}}]',15,1),(15,'2026-01-10 03:25:57.441176','19','Irina ZINCHENKO (VDC)',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\"]}}]',15,1),(16,'2026-01-10 03:26:23.168934','18','Augusto TANTALEAN (VDC)',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\"]}}]',15,1),(17,'2026-01-10 03:27:00.151039','17','Adrian WHITE (VDC)',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\"]}}]',15,1),(18,'2026-01-10 03:28:18.944483','21','Quentin MAILLE (EQUIPIER_JOUR)',2,'[{\"changed\": {\"fields\": [\"First name\", \"Last name\"]}}]',15,1),(19,'2026-01-10 03:29:32.289494','2','Francisco + Gabriela (Fija - Siempre juntas)',1,'[{\"added\": {}}]',16,1),(20,'2026-01-10 03:29:50.689170','3','Inés + Dorian (Fija - Siempre juntas)',1,'[{\"added\": {}}]',16,1),(21,'2026-01-10 03:38:29.814554','1','DEPART - Salida',2,'[{\"changed\": {\"fields\": [\"Base minutes\"]}}]',8,1),(22,'2026-01-10 03:38:42.511523','2','RECOUCH - Recouch',2,'[{\"changed\": {\"fields\": [\"Base minutes\"]}}]',8,1),(23,'2026-01-10 03:38:42.512454','5','COUVERTURE - Couverture',2,'[{\"changed\": {\"fields\": [\"Base minutes\"]}}]',8,1),(24,'2026-01-10 03:49:18.380352','14','Francisco BLANCO (VDC)',2,'[{\"changed\": {\"fields\": [\"Role\"]}}]',15,1),(25,'2026-01-10 03:49:40.966692','15','Inés LE BAIL (FDC)',2,'[{\"changed\": {\"fields\": [\"Role\"]}}]',15,1),(26,'2026-01-10 03:50:18.581084','10','Dorian PERRIER (VDC)',2,'[{\"changed\": {\"fields\": [\"Role\"]}}]',15,1),(27,'2026-01-10 03:50:57.969194','19','Irina ZINCHENKO (FDC)',2,'[{\"changed\": {\"fields\": [\"Role\"]}}]',15,1),(28,'2026-01-10 04:34:01.805018','18','Augusto TANTALEAN (VDC)',2,'[{\"changed\": {\"fields\": [\"Allowed blocks\"]}}]',15,1),(29,'2026-01-10 04:37:14.671029','18','Augusto TANTALEAN (VDC)',2,'[{\"changed\": {\"fields\": [\"Fixed days off\"]}}]',15,1),(30,'2026-01-10 04:43:26.256209','18','Augusto TANTALEAN (VDC)',2,'[]',15,1),(31,'2026-01-10 19:59:28.645631','5','COUVERTURE - Couverture',2,'[{\"changed\": {\"fields\": [\"Base minutes\"]}}]',8,1),(32,'2026-01-11 01:29:47.873179','15','Inés LE BAIL (FDC)',2,'[{\"changed\": {\"fields\": [\"Allowed blocks\"]}}]',15,1),(33,'2026-01-11 01:29:54.623543','10','Dorian PERRIER (VDC)',2,'[{\"changed\": {\"fields\": [\"Allowed blocks\"]}}]',15,1),(34,'2026-01-11 09:59:10.752479','19','FDC_TARDE_CORTO (14:00-21:30)',2,'[{\"changed\": {\"fields\": [\"Start time\", \"End time\"]}}]',18,1),(35,'2026-01-11 09:59:24.499582','12','FDC_TARDE (22:00-22:30)',2,'[{\"changed\": {\"fields\": [\"Start time\", \"End time\"]}}]',18,1),(36,'2026-01-11 10:00:00.483587','21','VDC_TARDE_CORTO (14:00-21:30)',2,'[{\"changed\": {\"fields\": [\"Start time\", \"End time\"]}}]',18,1),(37,'2026-01-11 10:00:21.968477','14','VDC_TARDE (14:00-22:30)',2,'[{\"changed\": {\"fields\": [\"Start time\", \"End time\"]}}]',18,1),(38,'2026-01-11 10:00:43.583871','12','FDC_TARDE (14:00-22:30)',2,'[{\"changed\": {\"fields\": [\"Start time\"]}}]',18,1);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(9,'core','building'),(13,'core','dayofweek'),(12,'core','room'),(11,'core','roomtype'),(8,'core','tasktype'),(7,'core','timeblock'),(10,'core','zone'),(31,'planning','dailyloadsummary'),(29,'planning','dailyplan'),(32,'planning','planningalert'),(28,'planning','shiftassignment'),(30,'planning','taskassignment'),(27,'planning','weekplan'),(22,'rooms','protelimportlog'),(20,'rooms','roomdailystate'),(21,'rooms','roomdailytask'),(25,'rules','elasticityrule'),(26,'rules','planningparameter'),(23,'rules','tasktimerule'),(24,'rules','zoneassignmentrule'),(6,'sessions','session'),(19,'shifts','shiftsubblock'),(18,'shifts','shifttemplate'),(15,'staff','employee'),(17,'staff','employeeunavailability'),(14,'staff','role'),(16,'staff','team');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-01-08 11:02:55.750029'),(2,'auth','0001_initial','2026-01-08 11:02:55.834342'),(3,'admin','0001_initial','2026-01-08 11:02:55.854108'),(4,'admin','0002_logentry_remove_auto_add','2026-01-08 11:02:55.856829'),(5,'admin','0003_logentry_add_action_flag_choices','2026-01-08 11:02:55.859175'),(6,'contenttypes','0002_remove_content_type_name','2026-01-08 11:02:55.879961'),(7,'auth','0002_alter_permission_name_max_length','2026-01-08 11:02:55.889719'),(8,'auth','0003_alter_user_email_max_length','2026-01-08 11:02:55.896830'),(9,'auth','0004_alter_user_username_opts','2026-01-08 11:02:55.899081'),(10,'auth','0005_alter_user_last_login_null','2026-01-08 11:02:55.908459'),(11,'auth','0006_require_contenttypes_0002','2026-01-08 11:02:55.908977'),(12,'auth','0007_alter_validators_add_error_messages','2026-01-08 11:02:55.911139'),(13,'auth','0008_alter_user_username_max_length','2026-01-08 11:02:55.923258'),(14,'auth','0009_alter_user_last_name_max_length','2026-01-08 11:02:55.932025'),(15,'auth','0010_alter_group_name_max_length','2026-01-08 11:02:55.937543'),(16,'auth','0011_update_proxy_permissions','2026-01-08 11:02:55.945661'),(17,'auth','0012_alter_user_first_name_max_length','2026-01-08 11:02:55.954598'),(18,'sessions','0001_initial','2026-01-08 11:02:55.959065'),(19,'core','0001_initial','2026-01-08 11:03:10.976410'),(20,'staff','0001_initial','2026-01-08 11:03:11.097344'),(21,'shifts','0001_initial','2026-01-08 11:03:11.132538'),(22,'rooms','0001_initial','2026-01-08 11:03:11.175789'),(23,'planning','0001_initial','2026-01-08 11:03:11.304651'),(24,'rules','0001_initial','2026-01-08 11:03:11.337352'),(25,'shifts','0002_alter_shifttemplate_unique_together_and_more','2026-01-10 02:20:16.574466'),(26,'staff','0002_role_can_clean_rooms','2026-01-10 02:20:16.591584'),(27,'planning','0002_add_forecast_load_fields','2026-01-10 04:25:26.270301'),(28,'core','0002_add_time_to_timeblock','2026-01-10 04:47:16.436653'),(29,'core','0003_add_task_time_constraints','2026-01-10 04:51:25.538044'),(30,'core','0004_add_persons_required','2026-01-10 05:08:40.109172'),(31,'core','0005_add_shift_config','2026-01-10 05:15:55.944646'),(32,'core','0006_add_solo_minutes_to_tasktype','2026-01-11 00:26:50.520235');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('jo4dpp2a7o95diz7vo88tz88vn3hqs9b','.eJxVjDsOwjAQRO_iGlnxh_Wakp4zWOu1gwPIkeKkQtwdR0oBxTTz3sxbBNrWEraWlzAlcRFKnH67SPzMdQfpQfU-S57rukxR7oo8aJO3OeXX9XD_Dgq10tfaUgJvEqPKPdEOQIjWjOA0UOyMGRC9PxvHzhsHIxGbwTpUGFmLzxfW9jdh:1vdnpE:cNhW-MDMpZbd58_hlMQ9vMyl1v7NQUfIvMi55YTpCvU','2026-01-22 11:05:08.383236');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `planning_dailyloadsummary`
--

DROP TABLE IF EXISTS `planning_dailyloadsummary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `planning_dailyloadsummary` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `total_tasks` int unsigned NOT NULL,
  `total_minutes_required` int unsigned NOT NULL,
  `total_employees` int unsigned NOT NULL,
  `total_minutes_available` int unsigned NOT NULL,
  `calculated_at` datetime(6) NOT NULL,
  `time_block_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `planning_dailyloadsummary_date_time_block_id_8ba599e4_uniq` (`date`,`time_block_id`),
  KEY `planning_dailyloadsu_time_block_id_90f8a70a_fk_core_time` (`time_block_id`),
  CONSTRAINT `planning_dailyloadsu_time_block_id_90f8a70a_fk_core_time` FOREIGN KEY (`time_block_id`) REFERENCES `core_timeblock` (`id`),
  CONSTRAINT `planning_dailyloadsummary_chk_1` CHECK ((`total_tasks` >= 0)),
  CONSTRAINT `planning_dailyloadsummary_chk_2` CHECK ((`total_minutes_required` >= 0)),
  CONSTRAINT `planning_dailyloadsummary_chk_3` CHECK ((`total_employees` >= 0)),
  CONSTRAINT `planning_dailyloadsummary_chk_4` CHECK ((`total_minutes_available` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `planning_dailyloadsummary`
--

LOCK TABLES `planning_dailyloadsummary` WRITE;
/*!40000 ALTER TABLE `planning_dailyloadsummary` DISABLE KEYS */;
/*!40000 ALTER TABLE `planning_dailyloadsummary` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `planning_dailyplan`
--

DROP TABLE IF EXISTS `planning_dailyplan`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `planning_dailyplan` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `notes` longtext NOT NULL,
  `week_plan_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `date` (`date`),
  KEY `planning_dailyplan_week_plan_id_ddea6c36_fk_planning_weekplan_id` (`week_plan_id`),
  CONSTRAINT `planning_dailyplan_week_plan_id_ddea6c36_fk_planning_weekplan_id` FOREIGN KEY (`week_plan_id`) REFERENCES `planning_weekplan` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `planning_dailyplan`
--

LOCK TABLES `planning_dailyplan` WRITE;
/*!40000 ALTER TABLE `planning_dailyplan` DISABLE KEYS */;
/*!40000 ALTER TABLE `planning_dailyplan` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `planning_planningalert`
--

DROP TABLE IF EXISTS `planning_planningalert`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `planning_planningalert` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `alert_type` varchar(20) NOT NULL,
  `severity` varchar(10) NOT NULL,
  `title` varchar(200) NOT NULL,
  `message` longtext NOT NULL,
  `is_resolved` tinyint(1) NOT NULL,
  `resolved_at` datetime(6) DEFAULT NULL,
  `resolved_by` varchar(100) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `time_block_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `planning_planningale_time_block_id_b149f2e7_fk_core_time` (`time_block_id`),
  CONSTRAINT `planning_planningale_time_block_id_b149f2e7_fk_core_time` FOREIGN KEY (`time_block_id`) REFERENCES `core_timeblock` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=67 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `planning_planningalert`
--

LOCK TABLES `planning_planningalert` WRITE;
/*!40000 ALTER TABLE `planning_planningalert` DISABLE KEYS */;
INSERT INTO `planning_planningalert` VALUES (1,'2026-01-12','WARNING','LOW','Déficit de horas para Sebastien CAMESCASSE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.412442',NULL),(2,'2026-01-12','WARNING','LOW','Déficit de horas para Benjamin GUILLARD','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.413327',NULL),(3,'2026-01-12','WARNING','LOW','Déficit de horas para Christopher LADHUIE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.413513',NULL),(4,'2026-01-12','WARNING','LOW','Déficit de horas para Chertande LEONARD','Asignadas 0h de 42.0h objetivo (faltan 42.0h)',0,NULL,'','2026-01-10 23:39:06.413932',NULL),(5,'2026-01-12','WARNING','LOW','Déficit de horas para Quentin MAILLE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.414156',NULL),(6,'2026-01-12','WARNING','LOW','Déficit de horas para Steffi MONIT','Asignadas 0h de 41.0h objetivo (faltan 41.0h)',0,NULL,'','2026-01-10 23:39:06.414344',NULL),(7,'2026-01-12','WARNING','LOW','Déficit de horas para Cynthia ROMERO','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.414576',NULL),(8,'2026-01-12','WARNING','LOW','Déficit de horas para Marion VIDAL','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.414763',NULL),(9,'2026-01-12','WARNING','LOW','Déficit de horas para Adrian WHITE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.414954',NULL),(10,'2026-01-12','WARNING','LOW','Déficit de horas para Irina ZINCHENKO','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.415123',NULL),(11,'2026-01-12','WARNING','LOW','Déficit de horas para Ingrid PICAULT','Asignadas 0h de 45.0h objetivo (faltan 45.0h)',0,NULL,'','2026-01-10 23:39:06.415265',NULL),(12,'2026-01-12','WARNING','LOW','Déficit de horas para Augusto TANTALEAN','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.415425',NULL),(13,'2026-01-12','WARNING','LOW','Déficit de horas para Sebastien CAMESCASSE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.415610',NULL),(14,'2026-01-12','WARNING','LOW','Déficit de horas para Benjamin GUILLARD','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.415750',NULL),(15,'2026-01-12','WARNING','LOW','Déficit de horas para Christopher LADHUIE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.415937',NULL),(16,'2026-01-12','WARNING','LOW','Déficit de horas para Chertande LEONARD','Asignadas 0h de 42.0h objetivo (faltan 42.0h)',0,NULL,'','2026-01-10 23:39:06.416113',NULL),(17,'2026-01-12','WARNING','LOW','Déficit de horas para Quentin MAILLE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.416279',NULL),(18,'2026-01-12','WARNING','LOW','Déficit de horas para Steffi MONIT','Asignadas 0h de 41.0h objetivo (faltan 41.0h)',0,NULL,'','2026-01-10 23:39:06.416425',NULL),(19,'2026-01-12','WARNING','LOW','Déficit de horas para Cynthia ROMERO','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.416557',NULL),(20,'2026-01-12','WARNING','LOW','Déficit de horas para Marion VIDAL','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.416711',NULL),(21,'2026-01-12','WARNING','LOW','Déficit de horas para Adrian WHITE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.416859',NULL),(22,'2026-01-12','WARNING','LOW','Déficit de horas para Irina ZINCHENKO','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:39:06.417014',NULL),(23,'2026-01-12','WARNING','LOW','Déficit de horas para Sebastien CAMESCASSE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.977590',NULL),(24,'2026-01-12','WARNING','LOW','Déficit de horas para Benjamin GUILLARD','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.978096',NULL),(25,'2026-01-12','WARNING','LOW','Déficit de horas para Christopher LADHUIE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.978380',NULL),(26,'2026-01-12','WARNING','LOW','Déficit de horas para Chertande LEONARD','Asignadas 0h de 42.0h objetivo (faltan 42.0h)',0,NULL,'','2026-01-10 23:40:10.978732',NULL),(27,'2026-01-12','WARNING','LOW','Déficit de horas para Quentin MAILLE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.979121',NULL),(28,'2026-01-12','WARNING','LOW','Déficit de horas para Steffi MONIT','Asignadas 0h de 41.0h objetivo (faltan 41.0h)',0,NULL,'','2026-01-10 23:40:10.979276',NULL),(29,'2026-01-12','WARNING','LOW','Déficit de horas para Cynthia ROMERO','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.979414',NULL),(30,'2026-01-12','WARNING','LOW','Déficit de horas para Marion VIDAL','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.979576',NULL),(31,'2026-01-12','WARNING','LOW','Déficit de horas para Adrian WHITE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.979720',NULL),(32,'2026-01-12','WARNING','LOW','Déficit de horas para Irina ZINCHENKO','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.979871',NULL),(33,'2026-01-12','WARNING','LOW','Déficit de horas para Ingrid PICAULT','Asignadas 0h de 45.0h objetivo (faltan 45.0h)',0,NULL,'','2026-01-10 23:40:10.980027',NULL),(34,'2026-01-12','WARNING','LOW','Déficit de horas para Augusto TANTALEAN','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.980167',NULL),(35,'2026-01-12','WARNING','LOW','Déficit de horas para Sebastien CAMESCASSE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.980327',NULL),(36,'2026-01-12','WARNING','LOW','Déficit de horas para Benjamin GUILLARD','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.980481',NULL),(37,'2026-01-12','WARNING','LOW','Déficit de horas para Christopher LADHUIE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.980656',NULL),(38,'2026-01-12','WARNING','LOW','Déficit de horas para Chertande LEONARD','Asignadas 0h de 42.0h objetivo (faltan 42.0h)',0,NULL,'','2026-01-10 23:40:10.980816',NULL),(39,'2026-01-12','WARNING','LOW','Déficit de horas para Quentin MAILLE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.980956',NULL),(40,'2026-01-12','WARNING','LOW','Déficit de horas para Steffi MONIT','Asignadas 0h de 41.0h objetivo (faltan 41.0h)',0,NULL,'','2026-01-10 23:40:10.981097',NULL),(41,'2026-01-12','WARNING','LOW','Déficit de horas para Cynthia ROMERO','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.981249',NULL),(42,'2026-01-12','WARNING','LOW','Déficit de horas para Marion VIDAL','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.981396',NULL),(43,'2026-01-12','WARNING','LOW','Déficit de horas para Adrian WHITE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.981535',NULL),(44,'2026-01-12','WARNING','LOW','Déficit de horas para Irina ZINCHENKO','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:40:10.981686',NULL),(45,'2026-01-12','WARNING','LOW','Déficit de horas para Sebastien CAMESCASSE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.362654',NULL),(46,'2026-01-12','WARNING','LOW','Déficit de horas para Benjamin GUILLARD','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.362947',NULL),(47,'2026-01-12','WARNING','LOW','Déficit de horas para Christopher LADHUIE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.363094',NULL),(48,'2026-01-12','WARNING','LOW','Déficit de horas para Chertande LEONARD','Asignadas 0h de 42.0h objetivo (faltan 42.0h)',0,NULL,'','2026-01-10 23:42:24.363253',NULL),(49,'2026-01-12','WARNING','LOW','Déficit de horas para Quentin MAILLE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.363431',NULL),(50,'2026-01-12','WARNING','LOW','Déficit de horas para Steffi MONIT','Asignadas 0h de 41.0h objetivo (faltan 41.0h)',0,NULL,'','2026-01-10 23:42:24.363589',NULL),(51,'2026-01-12','WARNING','LOW','Déficit de horas para Cynthia ROMERO','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.363727',NULL),(52,'2026-01-12','WARNING','LOW','Déficit de horas para Marion VIDAL','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.363873',NULL),(53,'2026-01-12','WARNING','LOW','Déficit de horas para Adrian WHITE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.364009',NULL),(54,'2026-01-12','WARNING','LOW','Déficit de horas para Irina ZINCHENKO','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.364157',NULL),(55,'2026-01-12','WARNING','LOW','Déficit de horas para Ingrid PICAULT','Asignadas 0h de 45.0h objetivo (faltan 45.0h)',0,NULL,'','2026-01-10 23:42:24.364292',NULL),(56,'2026-01-12','WARNING','LOW','Déficit de horas para Augusto TANTALEAN','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.364439',NULL),(57,'2026-01-12','WARNING','LOW','Déficit de horas para Sebastien CAMESCASSE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.364617',NULL),(58,'2026-01-12','WARNING','LOW','Déficit de horas para Benjamin GUILLARD','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.364764',NULL),(59,'2026-01-12','WARNING','LOW','Déficit de horas para Christopher LADHUIE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.364918',NULL),(60,'2026-01-12','WARNING','LOW','Déficit de horas para Chertande LEONARD','Asignadas 0h de 42.0h objetivo (faltan 42.0h)',0,NULL,'','2026-01-10 23:42:24.365062',NULL),(61,'2026-01-12','WARNING','LOW','Déficit de horas para Quentin MAILLE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.365201',NULL),(62,'2026-01-12','WARNING','LOW','Déficit de horas para Steffi MONIT','Asignadas 0h de 41.0h objetivo (faltan 41.0h)',0,NULL,'','2026-01-10 23:42:24.365351',NULL),(63,'2026-01-12','WARNING','LOW','Déficit de horas para Cynthia ROMERO','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.365484',NULL),(64,'2026-01-12','WARNING','LOW','Déficit de horas para Marion VIDAL','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.365646',NULL),(65,'2026-01-12','WARNING','LOW','Déficit de horas para Adrian WHITE','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.365792',NULL),(66,'2026-01-12','WARNING','LOW','Déficit de horas para Irina ZINCHENKO','Asignadas 0h de 39.0h objetivo (faltan 39.0h)',0,NULL,'','2026-01-10 23:42:24.365920',NULL);
/*!40000 ALTER TABLE `planning_planningalert` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `planning_shiftassignment`
--

DROP TABLE IF EXISTS `planning_shiftassignment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `planning_shiftassignment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `assigned_hours` decimal(4,2) NOT NULL,
  `is_day_off` tinyint(1) NOT NULL,
  `notes` longtext NOT NULL,
  `employee_id` bigint DEFAULT NULL,
  `shift_template_id` bigint NOT NULL,
  `team_id` bigint DEFAULT NULL,
  `week_plan_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `planning_shiftassign_employee_id_3ac85766_fk_staff_emp` (`employee_id`),
  KEY `planning_shiftassign_shift_template_id_ce7e5543_fk_shifts_sh` (`shift_template_id`),
  KEY `planning_shiftassignment_team_id_632dbd7f_fk_staff_team_id` (`team_id`),
  KEY `planning_shiftassign_week_plan_id_1cee1f5c_fk_planning_` (`week_plan_id`),
  CONSTRAINT `planning_shiftassign_employee_id_3ac85766_fk_staff_emp` FOREIGN KEY (`employee_id`) REFERENCES `staff_employee` (`id`),
  CONSTRAINT `planning_shiftassign_shift_template_id_ce7e5543_fk_shifts_sh` FOREIGN KEY (`shift_template_id`) REFERENCES `shifts_shifttemplate` (`id`),
  CONSTRAINT `planning_shiftassign_week_plan_id_1cee1f5c_fk_planning_` FOREIGN KEY (`week_plan_id`) REFERENCES `planning_weekplan` (`id`),
  CONSTRAINT `planning_shiftassignment_team_id_632dbd7f_fk_staff_team_id` FOREIGN KEY (`team_id`) REFERENCES `staff_team` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6523 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `planning_shiftassignment`
--

LOCK TABLES `planning_shiftassignment` WRITE;
/*!40000 ALTER TABLE `planning_shiftassignment` DISABLE KEYS */;
INSERT INTO `planning_shiftassignment` VALUES (6473,'2026-01-17',8.00,0,'',14,13,NULL,96),(6474,'2026-01-17',8.00,0,'',13,11,NULL,96),(6475,'2026-01-18',8.00,0,'',14,13,NULL,96),(6476,'2026-01-18',8.00,0,'',13,11,NULL,96),(6477,'2026-01-16',8.00,0,'',14,13,NULL,96),(6478,'2026-01-16',8.00,0,'',13,11,NULL,96),(6479,'2026-01-14',8.00,0,'',14,13,NULL,96),(6480,'2026-01-14',8.00,0,'',13,11,NULL,96),(6481,'2026-01-15',7.00,0,'',14,20,NULL,96),(6482,'2026-01-15',7.00,0,'',13,18,NULL,96),(6483,'2026-01-17',8.00,0,'',15,11,NULL,96),(6484,'2026-01-17',8.00,0,'',10,13,NULL,96),(6485,'2026-01-18',8.00,0,'',15,11,NULL,96),(6486,'2026-01-18',8.00,0,'',10,13,NULL,96),(6487,'2026-01-16',8.00,0,'',15,11,NULL,96),(6488,'2026-01-16',8.00,0,'',10,13,NULL,96),(6489,'2026-01-12',8.00,0,'',15,11,NULL,96),(6490,'2026-01-12',8.00,0,'',10,13,NULL,96),(6491,'2026-01-13',7.00,0,'',15,18,NULL,96),(6492,'2026-01-13',7.00,0,'',10,20,NULL,96),(6493,'2026-01-17',8.00,0,'',16,14,NULL,96),(6494,'2026-01-17',8.00,0,'',17,14,NULL,96),(6495,'2026-01-17',8.00,0,'',11,12,NULL,96),(6496,'2026-01-18',8.00,0,'',16,14,NULL,96),(6497,'2026-01-18',8.00,0,'',17,14,NULL,96),(6498,'2026-01-18',8.00,0,'',12,12,NULL,96),(6499,'2026-01-16',8.00,0,'',16,14,NULL,96),(6500,'2026-01-16',8.00,0,'',17,14,NULL,96),(6501,'2026-01-14',8.00,0,'',19,12,NULL,96),(6502,'2026-01-14',8.00,0,'',11,12,NULL,96),(6503,'2026-01-12',8.00,0,'',16,14,NULL,96),(6504,'2026-01-12',8.00,0,'',17,14,NULL,96),(6505,'2026-01-13',8.00,0,'',12,12,NULL,96),(6506,'2026-01-13',8.00,0,'',19,12,NULL,96),(6507,'2026-01-15',7.00,0,'',16,21,NULL,96),(6508,'2026-01-15',7.00,0,'',17,21,NULL,96),(6509,'2026-01-15',8.00,0,'',12,12,NULL,96),(6510,'2026-01-14',8.00,0,'',18,13,NULL,96),(6511,'2026-01-17',8.00,0,'',18,13,NULL,96),(6512,'2026-01-18',8.00,0,'',18,13,NULL,96),(6513,'2026-01-16',8.00,0,'',18,13,NULL,96),(6514,'2026-01-15',7.00,0,'',18,20,NULL,96),(6515,'2026-01-18',8.00,0,'',11,12,NULL,96),(6516,'2026-01-12',8.00,0,'',11,11,NULL,96),(6517,'2026-01-13',7.00,0,'',11,18,NULL,96),(6518,'2026-01-17',8.00,0,'',19,12,NULL,96),(6519,'2026-01-18',8.00,0,'',19,12,NULL,96),(6520,'2026-01-12',7.00,0,'',19,19,NULL,96),(6521,'2026-01-14',8.00,0,'',12,12,NULL,96),(6522,'2026-01-12',7.00,0,'',12,18,NULL,96);
/*!40000 ALTER TABLE `planning_shiftassignment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `planning_taskassignment`
--

DROP TABLE IF EXISTS `planning_taskassignment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `planning_taskassignment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `order_in_assignment` int unsigned NOT NULL,
  `status` varchar(20) NOT NULL,
  `started_at` time(6) DEFAULT NULL,
  `completed_at` time(6) DEFAULT NULL,
  `notes` longtext NOT NULL,
  `daily_plan_id` bigint NOT NULL,
  `employee_id` bigint DEFAULT NULL,
  `room_task_id` bigint NOT NULL,
  `team_id` bigint DEFAULT NULL,
  `zone_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `planning_taskassignm_daily_plan_id_9710aa3d_fk_planning_` (`daily_plan_id`),
  KEY `planning_taskassignm_employee_id_b38dd8f1_fk_staff_emp` (`employee_id`),
  KEY `planning_taskassignm_room_task_id_85b1109e_fk_rooms_roo` (`room_task_id`),
  KEY `planning_taskassignment_team_id_ae2b614f_fk_staff_team_id` (`team_id`),
  KEY `planning_taskassignment_zone_id_328c6ea6_fk_core_zone_id` (`zone_id`),
  CONSTRAINT `planning_taskassignm_daily_plan_id_9710aa3d_fk_planning_` FOREIGN KEY (`daily_plan_id`) REFERENCES `planning_dailyplan` (`id`),
  CONSTRAINT `planning_taskassignm_employee_id_b38dd8f1_fk_staff_emp` FOREIGN KEY (`employee_id`) REFERENCES `staff_employee` (`id`),
  CONSTRAINT `planning_taskassignm_room_task_id_85b1109e_fk_rooms_roo` FOREIGN KEY (`room_task_id`) REFERENCES `rooms_roomdailytask` (`id`),
  CONSTRAINT `planning_taskassignment_team_id_ae2b614f_fk_staff_team_id` FOREIGN KEY (`team_id`) REFERENCES `staff_team` (`id`),
  CONSTRAINT `planning_taskassignment_zone_id_328c6ea6_fk_core_zone_id` FOREIGN KEY (`zone_id`) REFERENCES `core_zone` (`id`),
  CONSTRAINT `planning_taskassignment_chk_1` CHECK ((`order_in_assignment` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `planning_taskassignment`
--

LOCK TABLES `planning_taskassignment` WRITE;
/*!40000 ALTER TABLE `planning_taskassignment` DISABLE KEYS */;
/*!40000 ALTER TABLE `planning_taskassignment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `planning_weekplan`
--

DROP TABLE IF EXISTS `planning_weekplan`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `planning_weekplan` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `week_start_date` date NOT NULL,
  `name` varchar(100) NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `created_by` varchar(100) NOT NULL,
  `published_at` datetime(6) DEFAULT NULL,
  `notes` longtext NOT NULL,
  `forecast_data` json DEFAULT NULL,
  `load_calculation` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `planning_weekplan_week_start_date_c61631ca_uniq` (`week_start_date`)
) ENGINE=InnoDB AUTO_INCREMENT=97 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `planning_weekplan`
--

LOCK TABLES `planning_weekplan` WRITE;
/*!40000 ALTER TABLE `planning_weekplan` DISABLE KEYS */;
INSERT INTO `planning_weekplan` VALUES (96,'2026-01-12','Semana 12/01/2026','DRAFT','2026-01-11 10:02:47.078083','2026-01-11 10:02:47.078097','',NULL,'','[{\"date\": \"2026-01-12\", \"arrivals\": 3, \"occupied\": 27, \"departures\": 3}, {\"date\": \"2026-01-13\", \"arrivals\": 1, \"occupied\": 28, \"departures\": 0}, {\"date\": \"2026-01-14\", \"arrivals\": 4, \"occupied\": 23, \"departures\": 9}, {\"date\": \"2026-01-15\", \"arrivals\": 8, \"occupied\": 30, \"departures\": 1}, {\"date\": \"2026-01-16\", \"arrivals\": 6, \"occupied\": 32, \"departures\": 4}, {\"date\": \"2026-01-17\", \"arrivals\": 7, \"occupied\": 30, \"departures\": 9}, {\"date\": \"2026-01-18\", \"arrivals\": 10, \"occupied\": 30, \"departures\": 10}]','{\"by_day\": {\"2026-01-12\": {\"tasks\": {\"DEPART\": {\"count\": 3, \"minutes\": 300}, \"RECOUCH\": {\"count\": 24, \"minutes\": 960}, \"COUVERTURE\": {\"count\": 27, \"minutes\": 405}}, \"shifts\": {\"DAY\": {\"hours\": 21.0, \"persons_needed\": 2}, \"EVENING\": {\"hours\": 6.8, \"persons_needed\": 2}}, \"day_name\": \"Lun\", \"total_hours\": 27.8}, \"2026-01-13\": {\"tasks\": {\"DEPART\": {\"count\": 0, \"minutes\": 0}, \"RECOUCH\": {\"count\": 27, \"minutes\": 1080}, \"COUVERTURE\": {\"count\": 28, \"minutes\": 420}}, \"shifts\": {\"DAY\": {\"hours\": 18.0, \"persons_needed\": 2}, \"EVENING\": {\"hours\": 7.0, \"persons_needed\": 2}}, \"day_name\": \"Mar\", \"total_hours\": 25.0}, \"2026-01-14\": {\"tasks\": {\"DEPART\": {\"count\": 9, \"minutes\": 900}, \"RECOUCH\": {\"count\": 19, \"minutes\": 760}, \"COUVERTURE\": {\"count\": 23, \"minutes\": 345}}, \"shifts\": {\"DAY\": {\"hours\": 27.7, \"persons_needed\": 2}, \"EVENING\": {\"hours\": 5.8, \"persons_needed\": 2}}, \"day_name\": \"Mié\", \"total_hours\": 33.4}, \"2026-01-15\": {\"tasks\": {\"DEPART\": {\"count\": 1, \"minutes\": 100}, \"RECOUCH\": {\"count\": 22, \"minutes\": 880}, \"COUVERTURE\": {\"count\": 30, \"minutes\": 450}}, \"shifts\": {\"DAY\": {\"hours\": 16.3, \"persons_needed\": 2}, \"EVENING\": {\"hours\": 7.5, \"persons_needed\": 2}}, \"day_name\": \"Jue\", \"total_hours\": 23.8}, \"2026-01-16\": {\"tasks\": {\"DEPART\": {\"count\": 4, \"minutes\": 400}, \"RECOUCH\": {\"count\": 26, \"minutes\": 1040}, \"COUVERTURE\": {\"count\": 32, \"minutes\": 480}}, \"shifts\": {\"DAY\": {\"hours\": 24.0, \"persons_needed\": 2}, \"EVENING\": {\"hours\": 8.0, \"persons_needed\": 2}}, \"day_name\": \"Vie\", \"total_hours\": 32.0}, \"2026-01-17\": {\"tasks\": {\"DEPART\": {\"count\": 9, \"minutes\": 900}, \"RECOUCH\": {\"count\": 23, \"minutes\": 920}, \"COUVERTURE\": {\"count\": 30, \"minutes\": 450}}, \"shifts\": {\"DAY\": {\"hours\": 30.3, \"persons_needed\": 3}, \"EVENING\": {\"hours\": 7.5, \"persons_needed\": 2}}, \"day_name\": \"Sáb\", \"total_hours\": 37.8}, \"2026-01-18\": {\"tasks\": {\"DEPART\": {\"count\": 10, \"minutes\": 1000}, \"RECOUCH\": {\"count\": 20, \"minutes\": 800}, \"COUVERTURE\": {\"count\": 30, \"minutes\": 450}}, \"shifts\": {\"DAY\": {\"hours\": 30.0, \"persons_needed\": 3}, \"EVENING\": {\"hours\": 7.5, \"persons_needed\": 2}}, \"day_name\": \"Dom\", \"total_hours\": 37.5}}, \"totals\": {\"total_hours\": 217.3, \"day_shift_hours\": 167.3, \"evening_shift_hours\": 50.0}}');
/*!40000 ALTER TABLE `planning_weekplan` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rooms_protelimportlog`
--

DROP TABLE IF EXISTS `rooms_protelimportlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rooms_protelimportlog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `filename` varchar(255) NOT NULL,
  `imported_at` datetime(6) NOT NULL,
  `imported_by` varchar(100) NOT NULL,
  `rows_processed` int unsigned NOT NULL,
  `rows_success` int unsigned NOT NULL,
  `rows_error` int unsigned NOT NULL,
  `date_from` date DEFAULT NULL,
  `date_to` date DEFAULT NULL,
  `errors` longtext NOT NULL,
  `status` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `rooms_protelimportlog_chk_1` CHECK ((`rows_processed` >= 0)),
  CONSTRAINT `rooms_protelimportlog_chk_2` CHECK ((`rows_success` >= 0)),
  CONSTRAINT `rooms_protelimportlog_chk_3` CHECK ((`rows_error` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rooms_protelimportlog`
--

LOCK TABLES `rooms_protelimportlog` WRITE;
/*!40000 ALTER TABLE `rooms_protelimportlog` DISABLE KEYS */;
/*!40000 ALTER TABLE `rooms_protelimportlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rooms_roomdailystate`
--

DROP TABLE IF EXISTS `rooms_roomdailystate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rooms_roomdailystate` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `occupancy_status` varchar(20) NOT NULL,
  `stay_day_number` int unsigned NOT NULL,
  `expected_checkout_time` time(6) DEFAULT NULL,
  `expected_checkin_time` time(6) DEFAULT NULL,
  `day_cleaning_status` varchar(20) NOT NULL,
  `night_expected_difficulty` varchar(20) NOT NULL,
  `is_vip` tinyint(1) NOT NULL,
  `notes` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `room_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `rooms_roomdailystate_date_room_id_f6f0c462_uniq` (`date`,`room_id`),
  KEY `rooms_roomdailystate_room_id_323eccd1_fk_core_room_id` (`room_id`),
  CONSTRAINT `rooms_roomdailystate_room_id_323eccd1_fk_core_room_id` FOREIGN KEY (`room_id`) REFERENCES `core_room` (`id`),
  CONSTRAINT `rooms_roomdailystate_chk_1` CHECK ((`stay_day_number` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rooms_roomdailystate`
--

LOCK TABLES `rooms_roomdailystate` WRITE;
/*!40000 ALTER TABLE `rooms_roomdailystate` DISABLE KEYS */;
/*!40000 ALTER TABLE `rooms_roomdailystate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rooms_roomdailytask`
--

DROP TABLE IF EXISTS `rooms_roomdailytask`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rooms_roomdailytask` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `estimated_minutes` int unsigned NOT NULL,
  `status` varchar(20) NOT NULL,
  `priority` int unsigned NOT NULL,
  `notes` longtext NOT NULL,
  `room_daily_state_id` bigint NOT NULL,
  `task_type_id` bigint NOT NULL,
  `time_block_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `rooms_roomdailytask_room_daily_state_id_30a99325_fk_rooms_roo` (`room_daily_state_id`),
  KEY `rooms_roomdailytask_task_type_id_872820fd_fk_core_tasktype_id` (`task_type_id`),
  KEY `rooms_roomdailytask_time_block_id_df469e95_fk_core_timeblock_id` (`time_block_id`),
  CONSTRAINT `rooms_roomdailytask_room_daily_state_id_30a99325_fk_rooms_roo` FOREIGN KEY (`room_daily_state_id`) REFERENCES `rooms_roomdailystate` (`id`),
  CONSTRAINT `rooms_roomdailytask_task_type_id_872820fd_fk_core_tasktype_id` FOREIGN KEY (`task_type_id`) REFERENCES `core_tasktype` (`id`),
  CONSTRAINT `rooms_roomdailytask_time_block_id_df469e95_fk_core_timeblock_id` FOREIGN KEY (`time_block_id`) REFERENCES `core_timeblock` (`id`),
  CONSTRAINT `rooms_roomdailytask_chk_1` CHECK ((`estimated_minutes` >= 0)),
  CONSTRAINT `rooms_roomdailytask_chk_2` CHECK ((`priority` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rooms_roomdailytask`
--

LOCK TABLES `rooms_roomdailytask` WRITE;
/*!40000 ALTER TABLE `rooms_roomdailytask` DISABLE KEYS */;
/*!40000 ALTER TABLE `rooms_roomdailytask` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rules_elasticityrule`
--

DROP TABLE IF EXISTS `rules_elasticityrule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rules_elasticityrule` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `elasticity_level` varchar(10) NOT NULL,
  `max_extra_hours_week` decimal(4,1) NOT NULL,
  `max_extra_hours_day` decimal(3,1) NOT NULL,
  `assignment_priority` int unsigned NOT NULL,
  `description` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `elasticity_level` (`elasticity_level`),
  CONSTRAINT `rules_elasticityrule_chk_1` CHECK ((`assignment_priority` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rules_elasticityrule`
--

LOCK TABLES `rules_elasticityrule` WRITE;
/*!40000 ALTER TABLE `rules_elasticityrule` DISABLE KEYS */;
INSERT INTO `rules_elasticityrule` VALUES (1,'LOW',0.0,0.0,1,''),(2,'MEDIUM',4.0,1.0,2,''),(3,'HIGH',8.0,2.0,3,'');
/*!40000 ALTER TABLE `rules_elasticityrule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rules_planningparameter`
--

DROP TABLE IF EXISTS `rules_planningparameter`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rules_planningparameter` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(50) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `value_type` varchar(20) NOT NULL,
  `value` varchar(200) NOT NULL,
  `category` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rules_planningparameter`
--

LOCK TABLES `rules_planningparameter` WRITE;
/*!40000 ALTER TABLE `rules_planningparameter` DISABLE KEYS */;
/*!40000 ALTER TABLE `rules_planningparameter` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rules_tasktimerule`
--

DROP TABLE IF EXISTS `rules_tasktimerule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rules_tasktimerule` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `condition` varchar(30) NOT NULL,
  `base_minutes` int unsigned DEFAULT NULL,
  `time_multiplier` decimal(3,2) NOT NULL,
  `priority` int unsigned NOT NULL,
  `description` longtext NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `room_type_id` bigint DEFAULT NULL,
  `task_type_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `rules_tasktimerule_room_type_id_8c26776c_fk_core_roomtype_id` (`room_type_id`),
  KEY `rules_tasktimerule_task_type_id_b6b87e53_fk_core_tasktype_id` (`task_type_id`),
  CONSTRAINT `rules_tasktimerule_room_type_id_8c26776c_fk_core_roomtype_id` FOREIGN KEY (`room_type_id`) REFERENCES `core_roomtype` (`id`),
  CONSTRAINT `rules_tasktimerule_task_type_id_b6b87e53_fk_core_tasktype_id` FOREIGN KEY (`task_type_id`) REFERENCES `core_tasktype` (`id`),
  CONSTRAINT `rules_tasktimerule_chk_1` CHECK ((`base_minutes` >= 0)),
  CONSTRAINT `rules_tasktimerule_chk_2` CHECK ((`priority` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rules_tasktimerule`
--

LOCK TABLES `rules_tasktimerule` WRITE;
/*!40000 ALTER TABLE `rules_tasktimerule` DISABLE KEYS */;
INSERT INTO `rules_tasktimerule` VALUES (1,'NONE',NULL,1.00,10,'Base DEPART',1,NULL,1),(2,'SUITE',NULL,1.50,10,'DEPART en Suite',1,3,1),(3,'VIP',NULL,1.20,10,'DEPART VIP',1,NULL,1),(4,'NONE',NULL,1.00,10,'Base COUVERTURE',1,NULL,5),(5,'RECOUCH_DECLINED',NULL,1.40,10,'COUVERTURE cuando recouch rechazado',1,NULL,5),(6,'VIP',NULL,1.30,10,'COUVERTURE VIP',1,NULL,5);
/*!40000 ALTER TABLE `rules_tasktimerule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rules_zoneassignmentrule`
--

DROP TABLE IF EXISTS `rules_zoneassignmentrule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rules_zoneassignmentrule` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(50) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `value_boolean` tinyint(1) DEFAULT NULL,
  `value_integer` int DEFAULT NULL,
  `value_text` varchar(200) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rules_zoneassignmentrule`
--

LOCK TABLES `rules_zoneassignmentrule` WRITE;
/*!40000 ALTER TABLE `rules_zoneassignmentrule` DISABLE KEYS */;
INSERT INTO `rules_zoneassignmentrule` VALUES (1,'COMPLETE_ZONE_FIRST','Completar zona antes de cambiar','',1,NULL,'',1),(2,'MAX_ZONES_PER_EMPLOYEE','Máximo de zonas por empleado','',NULL,3,'',1),(3,'ADJACENT_ZONES_PREFERRED','Preferir zonas adyacentes','',1,NULL,'',1),(4,'PAIR_SAME_ZONE','Pareja trabaja misma zona','',1,NULL,'',1);
/*!40000 ALTER TABLE `rules_zoneassignmentrule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shifts_shiftsubblock`
--

DROP TABLE IF EXISTS `shifts_shiftsubblock`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shifts_shiftsubblock` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(30) NOT NULL,
  `name` varchar(100) NOT NULL,
  `start_time` time(6) NOT NULL,
  `end_time` time(6) NOT NULL,
  `is_break` tinyint(1) NOT NULL,
  `order` int unsigned NOT NULL,
  `description` longtext NOT NULL,
  `shift_template_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `shifts_shiftsubblock_shift_template_id_f5098e0b_fk_shifts_sh` (`shift_template_id`),
  CONSTRAINT `shifts_shiftsubblock_shift_template_id_f5098e0b_fk_shifts_sh` FOREIGN KEY (`shift_template_id`) REFERENCES `shifts_shifttemplate` (`id`),
  CONSTRAINT `shifts_shiftsubblock_chk_1` CHECK ((`order` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shifts_shiftsubblock`
--

LOCK TABLES `shifts_shiftsubblock` WRITE;
/*!40000 ALTER TABLE `shifts_shiftsubblock` DISABLE KEYS */;
/*!40000 ALTER TABLE `shifts_shiftsubblock` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shifts_shifttemplate`
--

DROP TABLE IF EXISTS `shifts_shifttemplate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shifts_shifttemplate` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(30) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `start_time` time(6) NOT NULL,
  `end_time` time(6) NOT NULL,
  `break_start` time(6) DEFAULT NULL,
  `break_end` time(6) DEFAULT NULL,
  `break_minutes` int unsigned NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `role_id` bigint NOT NULL,
  `time_block_id` bigint NOT NULL,
  `max_daily_hours` int unsigned NOT NULL,
  `weekly_hours_target` int unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `shifts_shifttemplate_time_block_id_9deddca5_fk_core_timeblock_id` (`time_block_id`),
  KEY `shifts_shifttemplate_role_id_b7ced26a` (`role_id`),
  CONSTRAINT `shifts_shifttemplate_role_id_b7ced26a_fk_staff_role_id` FOREIGN KEY (`role_id`) REFERENCES `staff_role` (`id`),
  CONSTRAINT `shifts_shifttemplate_time_block_id_9deddca5_fk_core_timeblock_id` FOREIGN KEY (`time_block_id`) REFERENCES `core_timeblock` (`id`),
  CONSTRAINT `shifts_shifttemplate_chk_1` CHECK ((`break_minutes` >= 0)),
  CONSTRAINT `shifts_shifttemplate_chk_2` CHECK ((`max_daily_hours` >= 0)),
  CONSTRAINT `shifts_shifttemplate_chk_3` CHECK ((`weekly_hours_target` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shifts_shifttemplate`
--

LOCK TABLES `shifts_shifttemplate` WRITE;
/*!40000 ALTER TABLE `shifts_shifttemplate` DISABLE KEYS */;
INSERT INTO `shifts_shifttemplate` VALUES (6,'GG_DIA','GG Día','','08:00:00.000000','17:30:00.000000',NULL,NULL,0,1,5,1,9,45),(7,'ASST_MANANA','Assistante Mañana','','08:00:00.000000','16:30:00.000000',NULL,NULL,0,1,6,1,8,41),(8,'ASST_TARDE','Assistante Tarde','','14:00:00.000000','22:00:00.000000',NULL,NULL,0,1,6,2,8,41),(9,'GOUV_SOIR_MANANA','Gouv. Soir Mañana','','08:00:00.000000','16:30:00.000000',NULL,NULL,0,1,7,1,8,42),(10,'GOUV_SOIR_TARDE','Gouv. Soir Tarde','','14:00:00.000000','22:30:00.000000',NULL,NULL,0,1,7,2,8,42),(11,'FDC_MANANA','FDC Mañana','','09:00:00.000000','17:30:00.000000','12:30:00.000000','13:00:00.000000',30,1,8,1,8,39),(12,'FDC_TARDE','FDC Tarde','','14:00:00.000000','22:30:00.000000','18:30:00.000000','19:00:00.000000',30,1,8,2,8,39),(13,'VDC_MANANA','VDC Mañana','','09:00:00.000000','17:30:00.000000','12:30:00.000000','13:00:00.000000',30,1,9,1,8,39),(14,'VDC_TARDE','VDC Tarde','','14:00:00.000000','22:30:00.000000','18:30:00.000000','19:00:00.000000',30,1,9,2,8,39),(15,'EQ_JOUR_MANANA','Équipier Día Mañana','','09:00:00.000000','17:30:00.000000','12:30:00.000000','13:00:00.000000',30,1,10,1,8,39),(16,'EQ_JOUR_TARDE','Équipier Día Tarde','','13:30:00.000000','22:00:00.000000','18:30:00.000000','19:00:00.000000',30,1,10,2,8,39),(17,'EQ_NUIT','Équipier Noche','','22:00:00.000000','06:00:00.000000',NULL,NULL,0,1,11,3,8,39),(18,'FDC_MANANA_CORTO','FDC Mañana Corto (7h)','','09:00:00.000000','16:30:00.000000','12:30:00.000000','13:00:00.000000',30,1,8,1,8,39),(19,'FDC_TARDE_CORTO','FDC Tarde Corto (7h)','','14:00:00.000000','21:30:00.000000','18:30:00.000000','19:00:00.000000',30,1,8,2,8,39),(20,'VDC_MANANA_CORTO','VDC Mañana Corto (7h)','','09:00:00.000000','16:30:00.000000','12:30:00.000000','13:00:00.000000',30,1,9,1,8,39),(21,'VDC_TARDE_CORTO','VDC Tarde Corto (7h)','','14:00:00.000000','21:30:00.000000','18:30:00.000000','19:00:00.000000',30,1,9,2,8,39);
/*!40000 ALTER TABLE `shifts_shifttemplate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `staff_employee`
--

DROP TABLE IF EXISTS `staff_employee`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `staff_employee` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `employee_code` varchar(20) NOT NULL,
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `weekly_hours_target` decimal(4,1) NOT NULL,
  `elasticity` varchar(10) NOT NULL,
  `can_work_night` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `hire_date` date DEFAULT NULL,
  `notes` longtext NOT NULL,
  `role_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `employee_code` (`employee_code`),
  KEY `staff_employee_role_id_b54ea112_fk_staff_role_id` (`role_id`),
  CONSTRAINT `staff_employee_role_id_b54ea112_fk_staff_role_id` FOREIGN KEY (`role_id`) REFERENCES `staff_role` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staff_employee`
--

LOCK TABLES `staff_employee` WRITE;
/*!40000 ALTER TABLE `staff_employee` DISABLE KEYS */;
INSERT INTO `staff_employee` VALUES (7,'GG001','Ingrid','PICAULT',45.0,'LOW',0,1,NULL,'',5),(8,'ASST001','Steffi','MONIT',41.0,'MEDIUM',0,1,NULL,'',6),(9,'GSOIR001','Chertande','LEONARD',42.0,'MEDIUM',0,1,NULL,'',7),(10,'FDC001','Dorian','PERRIER',39.0,'MEDIUM',0,1,NULL,'',9),(11,'FDC002','Cynthia','ROMERO',39.0,'MEDIUM',0,1,NULL,'',8),(12,'FDC003','Marion','VIDAL',39.0,'MEDIUM',0,1,NULL,'',8),(13,'FDC004','Gabriela','CANADA',39.0,'MEDIUM',0,1,NULL,'',8),(14,'FDC005','Francisco','BLANCO',39.0,'MEDIUM',0,1,NULL,'',9),(15,'VDC001','Inés','LE BAIL',39.0,'MEDIUM',0,1,NULL,'',8),(16,'VDC002','Christopher','LADHUIE',39.0,'MEDIUM',0,1,NULL,'',9),(17,'VDC003','Adrian','WHITE',39.0,'MEDIUM',0,1,NULL,'',9),(18,'VDC004','Augusto','TANTALEAN',39.0,'MEDIUM',0,1,NULL,'',9),(19,'VDC005','Irina','ZINCHENKO',39.0,'MEDIUM',0,1,NULL,'',8),(20,'EQJOUR001','Benjamin','GUILLARD',39.0,'MEDIUM',0,1,NULL,'',10),(21,'EQJOUR002','Quentin','MAILLE',39.0,'MEDIUM',0,1,NULL,'',10),(22,'EQJOUR003','Sebastien','CAMESCASSE',39.0,'MEDIUM',0,1,NULL,'',10),(23,'EQNUIT001','Philippe','CABANEAU',39.0,'MEDIUM',1,1,NULL,'',11),(24,'EQNUIT002','Romain','LEGEARD',39.0,'MEDIUM',1,1,NULL,'',11);
/*!40000 ALTER TABLE `staff_employee` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `staff_employee_allowed_blocks`
--

DROP TABLE IF EXISTS `staff_employee_allowed_blocks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `staff_employee_allowed_blocks` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `employee_id` bigint NOT NULL,
  `timeblock_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `staff_employee_allowed_b_employee_id_timeblock_id_8a1887d8_uniq` (`employee_id`,`timeblock_id`),
  KEY `staff_employee_allow_timeblock_id_42cc0b3d_fk_core_time` (`timeblock_id`),
  CONSTRAINT `staff_employee_allow_employee_id_1d5286b9_fk_staff_emp` FOREIGN KEY (`employee_id`) REFERENCES `staff_employee` (`id`),
  CONSTRAINT `staff_employee_allow_timeblock_id_42cc0b3d_fk_core_time` FOREIGN KEY (`timeblock_id`) REFERENCES `core_timeblock` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staff_employee_allowed_blocks`
--

LOCK TABLES `staff_employee_allowed_blocks` WRITE;
/*!40000 ALTER TABLE `staff_employee_allowed_blocks` DISABLE KEYS */;
INSERT INTO `staff_employee_allowed_blocks` VALUES (9,7,1),(10,8,1),(11,8,2),(12,9,1),(13,9,2),(14,10,1),(16,11,1),(17,11,2),(18,12,1),(19,12,2),(20,13,1),(21,13,2),(22,14,1),(23,14,2),(24,15,1),(26,16,1),(27,16,2),(28,17,1),(29,17,2),(30,18,1),(32,19,1),(33,19,2),(34,20,1),(35,20,2),(36,21,1),(37,21,2),(38,22,1),(39,22,2),(40,23,3),(41,24,3);
/*!40000 ALTER TABLE `staff_employee_allowed_blocks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `staff_employee_eligible_tasks`
--

DROP TABLE IF EXISTS `staff_employee_eligible_tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `staff_employee_eligible_tasks` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `employee_id` bigint NOT NULL,
  `tasktype_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `staff_employee_eligible__employee_id_tasktype_id_e0132854_uniq` (`employee_id`,`tasktype_id`),
  KEY `staff_employee_eligi_tasktype_id_1808220e_fk_core_task` (`tasktype_id`),
  CONSTRAINT `staff_employee_eligi_employee_id_e2cb83aa_fk_staff_emp` FOREIGN KEY (`employee_id`) REFERENCES `staff_employee` (`id`),
  CONSTRAINT `staff_employee_eligi_tasktype_id_1808220e_fk_core_task` FOREIGN KEY (`tasktype_id`) REFERENCES `core_tasktype` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=90 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staff_employee_eligible_tasks`
--

LOCK TABLES `staff_employee_eligible_tasks` WRITE;
/*!40000 ALTER TABLE `staff_employee_eligible_tasks` DISABLE KEYS */;
INSERT INTO `staff_employee_eligible_tasks` VALUES (18,10,1),(19,10,2),(22,10,5),(24,11,1),(25,11,2),(28,11,5),(30,12,1),(31,12,2),(34,12,5),(36,13,1),(37,13,2),(40,13,5),(42,14,1),(43,14,2),(46,14,5),(48,15,1),(49,15,2),(52,15,5),(54,16,1),(55,16,2),(58,16,5),(60,17,1),(61,17,2),(64,17,5),(66,18,1),(67,18,2),(70,18,5),(72,19,1),(73,19,2),(76,19,5),(78,23,1),(79,23,2),(82,23,5),(84,24,1),(85,24,2),(88,24,5);
/*!40000 ALTER TABLE `staff_employee_eligible_tasks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `staff_employee_fixed_days_off`
--

DROP TABLE IF EXISTS `staff_employee_fixed_days_off`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `staff_employee_fixed_days_off` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `employee_id` bigint NOT NULL,
  `dayofweek_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `staff_employee_fixed_day_employee_id_dayofweek_id_ad55f243_uniq` (`employee_id`,`dayofweek_id`),
  KEY `staff_employee_fixed_dayofweek_id_c6789f61_fk_core_dayo` (`dayofweek_id`),
  CONSTRAINT `staff_employee_fixed_dayofweek_id_c6789f61_fk_core_dayo` FOREIGN KEY (`dayofweek_id`) REFERENCES `core_dayofweek` (`id`),
  CONSTRAINT `staff_employee_fixed_employee_id_6e60b434_fk_staff_emp` FOREIGN KEY (`employee_id`) REFERENCES `staff_employee` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staff_employee_fixed_days_off`
--

LOCK TABLES `staff_employee_fixed_days_off` WRITE;
/*!40000 ALTER TABLE `staff_employee_fixed_days_off` DISABLE KEYS */;
INSERT INTO `staff_employee_fixed_days_off` VALUES (5,18,1),(6,18,2);
/*!40000 ALTER TABLE `staff_employee_fixed_days_off` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `staff_employeeunavailability`
--

DROP TABLE IF EXISTS `staff_employeeunavailability`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `staff_employeeunavailability` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date_start` date NOT NULL,
  `date_end` date NOT NULL,
  `reason` varchar(20) NOT NULL,
  `notes` longtext NOT NULL,
  `employee_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `staff_employeeunavai_employee_id_506c11a4_fk_staff_emp` (`employee_id`),
  CONSTRAINT `staff_employeeunavai_employee_id_506c11a4_fk_staff_emp` FOREIGN KEY (`employee_id`) REFERENCES `staff_employee` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staff_employeeunavailability`
--

LOCK TABLES `staff_employeeunavailability` WRITE;
/*!40000 ALTER TABLE `staff_employeeunavailability` DISABLE KEYS */;
/*!40000 ALTER TABLE `staff_employeeunavailability` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `staff_role`
--

DROP TABLE IF EXISTS `staff_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `staff_role` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(30) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `display_order` int unsigned NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `can_clean_rooms` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  CONSTRAINT `staff_role_chk_1` CHECK ((`display_order` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staff_role`
--

LOCK TABLES `staff_role` WRITE;
/*!40000 ALTER TABLE `staff_role` DISABLE KEYS */;
INSERT INTO `staff_role` VALUES (5,'GG','Gouvernante Générale','Supervisión general y gestión',1,1,0),(6,'ASST_GG','Assistante GG','Asistente de gouvernante',2,1,0),(7,'GOUV_SOIR','Gouvernante du Soir','Supervisión turno tarde',3,1,0),(8,'FDC','Femme de Chambre','Housekeeping - limpieza habitaciones',4,1,1),(9,'VDC','Valet de Chambre','Housekeeping - limpieza habitaciones',5,1,1),(10,'EQUIPIER_JOUR','Équipier Jour','Áreas comunes y suministros - día',6,1,0),(11,'EQUIPIER_NUIT','Équipier Nuit','Áreas comunes y suministros - noche',7,1,1);
/*!40000 ALTER TABLE `staff_role` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `staff_role_allowed_blocks`
--

DROP TABLE IF EXISTS `staff_role_allowed_blocks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `staff_role_allowed_blocks` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `role_id` bigint NOT NULL,
  `timeblock_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `staff_role_allowed_blocks_role_id_timeblock_id_efc97c8f_uniq` (`role_id`,`timeblock_id`),
  KEY `staff_role_allowed_b_timeblock_id_0de3890e_fk_core_time` (`timeblock_id`),
  CONSTRAINT `staff_role_allowed_b_timeblock_id_0de3890e_fk_core_time` FOREIGN KEY (`timeblock_id`) REFERENCES `core_timeblock` (`id`),
  CONSTRAINT `staff_role_allowed_blocks_role_id_21078806_fk_staff_role_id` FOREIGN KEY (`role_id`) REFERENCES `staff_role` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staff_role_allowed_blocks`
--

LOCK TABLES `staff_role_allowed_blocks` WRITE;
/*!40000 ALTER TABLE `staff_role_allowed_blocks` DISABLE KEYS */;
INSERT INTO `staff_role_allowed_blocks` VALUES (10,5,1),(11,6,1),(12,6,2),(13,7,1),(14,7,2),(15,8,1),(16,8,2),(17,9,1),(18,9,2),(19,10,1),(20,10,2),(21,11,3);
/*!40000 ALTER TABLE `staff_role_allowed_blocks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `staff_team`
--

DROP TABLE IF EXISTS `staff_team`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `staff_team` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `team_type` varchar(20) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `notes` longtext NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staff_team`
--

LOCK TABLES `staff_team` WRITE;
/*!40000 ALTER TABLE `staff_team` DISABLE KEYS */;
INSERT INTO `staff_team` VALUES (2,'Francisco & Gabriela','FIXED',1,''),(3,'Dorian & Ines','FIXED',1,'');
/*!40000 ALTER TABLE `staff_team` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `staff_team_members`
--

DROP TABLE IF EXISTS `staff_team_members`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `staff_team_members` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `team_id` bigint NOT NULL,
  `employee_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `staff_team_members_team_id_employee_id_f4a86988_uniq` (`team_id`,`employee_id`),
  KEY `staff_team_members_employee_id_dc6ae36f_fk_staff_employee_id` (`employee_id`),
  CONSTRAINT `staff_team_members_employee_id_dc6ae36f_fk_staff_employee_id` FOREIGN KEY (`employee_id`) REFERENCES `staff_employee` (`id`),
  CONSTRAINT `staff_team_members_team_id_a9f5ef63_fk_staff_team_id` FOREIGN KEY (`team_id`) REFERENCES `staff_team` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staff_team_members`
--

LOCK TABLES `staff_team_members` WRITE;
/*!40000 ALTER TABLE `staff_team_members` DISABLE KEYS */;
INSERT INTO `staff_team_members` VALUES (3,2,13),(4,2,14),(5,3,10),(6,3,15);
/*!40000 ALTER TABLE `staff_team_members` ENABLE KEYS */;
UNLOCK TABLES;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-11 12:10:43
