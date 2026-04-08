-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: medicare_db
-- ------------------------------------------------------
-- Server version	8.0.45

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

--
-- Dumping data for table `admins`
--

LOCK TABLES `admins` WRITE;
/*!40000 ALTER TABLE `admins` DISABLE KEYS */;
INSERT INTO `admins` VALUES (1,'Nishan Bhattarai','nishan@clinic.com','$2b$12$E0ZrQAMHIyvU6f9gX//GPuPtPi8PhTh7FDUUgyXqoVZoh3e/pXFpO',NULL,'admin','2026-03-22 23:56:21');
/*!40000 ALTER TABLE `admins` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `appointments`
--

LOCK TABLES `appointments` WRITE;
/*!40000 ALTER TABLE `appointments` DISABLE KEYS */;
INSERT INTO `appointments` VALUES (1,1,1,'2026-03-22','09:00:00','','Completed',0,'2026-03-22 12:51:17','2026-03-22 01:39:45',NULL,'Unpaid',0.00),(2,1,1,'2026-03-23','13:30:00','','Completed',0,'2026-03-23 02:12:28','2026-03-23 02:09:22',NULL,'Unpaid',0.00),(3,1,1,'2026-03-23','14:00:00','','Completed',0,'2026-03-23 02:16:03','2026-03-23 02:14:33',NULL,'Unpaid',0.00),(4,1,2,'2026-03-23','10:00:00','','No-Show',0,NULL,'2026-03-23 02:20:36',NULL,'Unpaid',0.00),(5,2,1,'2026-03-25','16:30:00','','Cancelled',0,NULL,'2026-03-23 02:39:14',NULL,'Unpaid',0.00),(6,1,1,'2026-04-04','14:30:00','','Cancelled',0,NULL,'2026-03-23 03:35:08',NULL,'Unpaid',0.00),(7,1,3,'2026-03-29','16:00:00','','Cancelled',0,NULL,'2026-03-23 03:35:37',NULL,'Unpaid',0.00),(8,1,2,'2026-03-23','15:00:00','','No-Show',0,NULL,'2026-03-23 03:38:32',NULL,'Unpaid',0.00),(9,1,1,'2026-03-24','11:30:00','','No-Show',0,NULL,'2026-03-23 04:08:57','pi_3TDzkfPBaA4JeKvw15FBhQhJ','Paid',75.00),(10,1,1,'2026-03-25','15:00:00','','Cancelled',0,NULL,'2026-03-23 04:09:46','pi_3TDzoCPBaA4JeKvw0aBrd6jA','Paid',75.00),(11,1,1,'2026-03-23','14:30:00','','No-Show',0,NULL,'2026-03-23 04:12:19','pi_3TDzqePBaA4JeKvw2Ukl3sPA','Paid',75.00),(12,2,1,'2026-03-23','15:30:00','','No-Show',0,NULL,'2026-03-23 04:42:29','pi_3TE0JqPBaA4JeKvw2829BbDp','Paid',75.00),(13,1,1,'2026-03-24','09:00:00','','No-Show',0,NULL,'2026-03-23 13:41:16','pi_3TE8jFPBaA4JeKvw2xnr4Fis','Paid',75.00),(14,1,1,'2026-03-24','09:30:00','','No-Show',0,NULL,'2026-03-23 22:24:47','pi_3TEGttPBaA4JeKvw27q5yLvj','Paid',75.00),(15,1,1,'2026-03-25','10:30:00','','Completed',0,'2026-03-24 23:43:32','2026-03-24 23:36:56','pi_3TEeVGPBaA4JeKvw1dmKW9eI','Paid',75.00),(16,1,1,'2026-03-25','11:00:00','','No-Show',0,NULL,'2026-03-25 00:00:19','pi_3TEertPBaA4JeKvw0QQdF9xB','Paid',75.00),(17,3,1,'2026-04-01','09:30:00','','No-Show',0,NULL,'2026-03-31 12:20:16','pi_3TH1HFPBaA4JeKvw0FZgtH1Z','Paid',75.00);
/*!40000 ALTER TABLE `appointments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `audit_logs`
--

LOCK TABLES `audit_logs` WRITE;
/*!40000 ALTER TABLE `audit_logs` DISABLE KEYS */;
INSERT INTO `audit_logs` VALUES (1,1,'admin','Login_Success',1,'admins','127.0.0.1','2026-03-22 13:34:04'),(2,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-22 13:36:51'),(3,1,'admin','Login_Success',1,'admins','127.0.0.1','2026-03-22 13:37:03'),(4,1,'admin','Logout',1,'admins','127.0.0.1','2026-03-22 13:38:19'),(5,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-22 13:38:26'),(6,1,'patient','Logout',1,'patients','127.0.0.1','2026-03-22 13:39:11'),(7,1,'admin','Login_Success',1,'admins','127.0.0.1','2026-03-22 13:39:36'),(8,1,'admin','Logout',1,'admins','127.0.0.1','2026-03-22 13:42:05'),(9,1,'admin','Login_Success',1,'admins','127.0.0.1','2026-03-22 14:27:14'),(10,1,'admin','Logout',1,'admins','127.0.0.1','2026-03-22 14:39:42'),(11,1,'admin','Login_Success',1,'admins','127.0.0.1','2026-03-22 14:39:58'),(12,1,'admin','Login_Success',1,'admins','127.0.0.1','2026-03-23 01:48:40'),(13,1,'admin','Logout',1,'admins','127.0.0.1','2026-03-23 01:48:49'),(14,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-23 01:48:53'),(15,1,'patient','Logout',1,'patients','127.0.0.1','2026-03-23 02:02:52'),(16,1,'admin','Login_Success',1,'admins','127.0.0.1','2026-03-23 02:03:01'),(17,1,'admin','Logout',1,'admins','127.0.0.1','2026-03-23 02:04:39'),(18,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-23 02:04:47'),(19,1,'doctor','Logout',1,'doctors','127.0.0.1','2026-03-23 02:05:04'),(20,1,'admin','Login_Success',1,'admins','127.0.0.1','2026-03-23 02:05:08'),(21,1,'admin','Logout',1,'admins','127.0.0.1','2026-03-23 02:05:46'),(22,1,'admin','Login_Success',1,'admins','127.0.0.1','2026-03-23 02:05:51'),(23,1,'admin','Logout',1,'admins','127.0.0.1','2026-03-23 02:07:56'),(24,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-23 02:08:04'),(25,1,'doctor','Logout',1,'doctors','127.0.0.1','2026-03-23 02:08:16'),(26,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-23 02:08:21'),(27,1,'patient','Logout',1,'patients','127.0.0.1','2026-03-23 02:10:30'),(28,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-23 02:10:36'),(29,1,'doctor','Logout',1,'doctors','127.0.0.1','2026-03-23 02:12:32'),(30,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-23 02:12:40'),(31,1,'patient','Logout',1,'patients','127.0.0.1','2026-03-23 02:14:49'),(32,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-23 02:15:02'),(33,1,'doctor','Logout',1,'doctors','127.0.0.1','2026-03-23 02:16:08'),(34,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-23 02:16:13'),(35,1,'patient','Logout',1,'patients','127.0.0.1','2026-03-23 02:20:56'),(36,1,'admin','Login_Success',1,'admins','127.0.0.1','2026-03-23 02:21:03'),(37,1,'admin','Logout',1,'admins','127.0.0.1','2026-03-23 02:31:51'),(38,1,'admin','Login_Success',1,'admins','127.0.0.1','2026-03-23 02:32:27'),(39,1,'admin','Logout',1,'admins','127.0.0.1','2026-03-23 02:32:42'),(40,2,'patient','Login_Success',2,'patients','127.0.0.1','2026-03-23 02:38:41'),(41,2,'patient','Logout',2,'patients','127.0.0.1','2026-03-23 02:39:36'),(42,1,'admin','Login_Success',1,'admins','127.0.0.1','2026-03-23 02:39:44'),(43,1,'admin','Doctor_Edited',3,'doctors','127.0.0.1','2026-03-23 03:06:32'),(44,1,'admin','Doctor_Edited',1,'doctors','127.0.0.1','2026-03-23 03:07:30'),(45,1,'admin','Doctor_Edited',4,'doctors','127.0.0.1','2026-03-23 03:07:48'),(46,1,'admin','Doctor_Edited',2,'doctors','127.0.0.1','2026-03-23 03:08:14'),(47,1,'admin','Doctor_Edited',4,'doctors','127.0.0.1','2026-03-23 03:11:56'),(48,1,'admin','Doctor_Edited',2,'doctors','127.0.0.1','2026-03-23 03:12:27'),(49,1,'admin','Doctor_Edited',3,'doctors','127.0.0.1','2026-03-23 03:12:39'),(50,1,'admin','Logout',1,'admins','127.0.0.1','2026-03-23 03:12:46'),(51,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-23 03:12:52'),(52,1,'patient','Logout',1,'patients','127.0.0.1','2026-03-23 03:31:05'),(53,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-23 03:31:27'),(54,1,'doctor','Logout',1,'doctors','127.0.0.1','2026-03-23 03:32:05'),(55,1,'admin','Login_Success',1,'admins','127.0.0.1','2026-03-23 03:32:11'),(56,1,'admin','Logout',1,'admins','127.0.0.1','2026-03-23 03:32:53'),(57,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-23 03:33:06'),(58,1,'doctor','Logout',1,'doctors','127.0.0.1','2026-03-23 03:33:35'),(59,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-23 03:33:52'),(60,1,'patient','Logout',1,'patients','127.0.0.1','2026-03-23 03:36:11'),(61,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-23 03:36:25'),(62,1,'doctor','Logout',1,'doctors','127.0.0.1','2026-03-23 03:36:44'),(63,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-23 03:36:49'),(64,1,'patient','Logout',1,'patients','127.0.0.1','2026-03-23 04:09:50'),(65,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-23 04:09:57'),(66,1,'doctor','Logout',1,'doctors','127.0.0.1','2026-03-23 04:10:13'),(67,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-23 04:10:17'),(68,1,'patient','Logout',1,'patients','127.0.0.1','2026-03-23 04:10:50'),(69,1,'admin','Login_Success',1,'admins','127.0.0.1','2026-03-23 04:10:54'),(70,1,'admin','Logout',1,'admins','127.0.0.1','2026-03-23 04:12:26'),(71,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-23 04:12:33'),(72,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-23 04:15:54'),(73,1,'patient','Logout',1,'patients','127.0.0.1','2026-03-23 04:40:50'),(74,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-23 04:40:57'),(75,1,'doctor','Logout',1,'doctors','127.0.0.1','2026-03-23 04:41:22'),(76,2,'patient','Login_Success',2,'patients','127.0.0.1','2026-03-23 04:41:30'),(77,2,'patient','Logout',2,'patients','127.0.0.1','2026-03-23 04:54:01'),(78,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-23 04:54:07'),(79,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-23 04:54:14'),(80,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-23 12:44:34'),(81,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-23 13:07:29'),(82,2,'patient','Login_Success',2,'patients','127.0.0.1','2026-03-23 13:10:49'),(83,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-23 13:36:09'),(84,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-23 22:18:09'),(85,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-23 22:19:47'),(86,1,'patient','Logout',1,'patients','127.0.0.1','2026-03-23 22:21:12'),(87,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-23 22:21:25'),(88,1,'patient','Login_Failed',1,'patients','127.0.0.1','2026-03-23 22:40:30'),(89,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-23 22:40:38'),(90,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-23 22:41:09'),(91,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-24 23:32:54'),(92,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-24 23:35:10'),(93,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-24 23:35:59'),(94,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-24 23:36:01'),(95,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-24 23:58:37'),(96,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-24 23:59:40'),(97,1,'doctor','Logout',1,'doctors','127.0.0.1','2026-03-25 00:10:02'),(98,3,'patient','Patient_Registered',3,'patients','127.0.0.1','2026-03-25 00:10:37'),(99,3,'patient','Login_Success',3,'patients','127.0.0.1','2026-03-25 00:10:47'),(100,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-25 00:15:39'),(101,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-25 00:20:11'),(102,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-03-31 11:49:16'),(103,3,'patient','Login_Success',3,'patients','127.0.0.1','2026-03-31 12:13:43'),(104,3,'patient','Login_Success',3,'patients','127.0.0.1','2026-03-31 12:28:19'),(105,3,'patient','Logout',3,'patients','127.0.0.1','2026-03-31 12:28:32'),(106,1,'doctor','Login_Success',1,'doctors','127.0.0.1','2026-03-31 12:29:46'),(107,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-04-06 14:19:07'),(108,3,'patient','Login_Success',3,'patients','127.0.0.1','2026-04-06 14:31:29'),(109,3,'patient','Logout',3,'patients','127.0.0.1','2026-04-06 14:58:06'),(110,1,'admin','Login_Success',1,'admins','127.0.0.1','2026-04-06 14:58:39'),(111,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-04-07 13:33:32'),(112,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-04-07 13:38:35'),(113,1,'patient','Login_Failed',1,'patients','127.0.0.1','2026-04-07 13:51:24'),(114,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-04-07 13:51:39'),(115,1,'patient','Login_Success',1,'patients','127.0.0.1','2026-04-07 14:15:46');
/*!40000 ALTER TABLE `audit_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `call_sessions`
--

LOCK TABLES `call_sessions` WRITE;
/*!40000 ALTER TABLE `call_sessions` DISABLE KEYS */;
INSERT INTO `call_sessions` VALUES (2,12,2,1,'a8ec1937-cd65-46be-ab93-a89b246a009c','video','active','2026-03-23 04:59:07',NULL,NULL,'2026-03-23 04:49:35'),(6,13,1,1,'4ebfb826-5789-4494-afdc-bf7c97790146','video','ended','2026-03-23 22:29:23','2026-03-23 22:29:44',21,'2026-03-23 22:29:21'),(9,14,1,1,'94fab87b-b1d9-4a9a-bc4b-f90859da0b27','video','ended','2026-03-23 22:41:17','2026-03-23 22:42:20',63,'2026-03-23 22:40:45'),(10,15,1,1,'cc935b55-ac36-4e7d-bf97-b2bb7caf924b','video','ended','2026-03-24 23:37:20','2026-03-24 23:37:45',25,'2026-03-24 23:37:04'),(11,16,1,1,'31f9feb0-c02b-4d43-92a0-af4b7d0b6df3','video','ended','2026-03-25 00:01:32','2026-03-25 00:01:52',20,'2026-03-25 00:01:16');
/*!40000 ALTER TABLE `call_sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `cancellations`
--

LOCK TABLES `cancellations` WRITE;
/*!40000 ALTER TABLE `cancellations` DISABLE KEYS */;
/*!40000 ALTER TABLE `cancellations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `chat_attachments`
--

LOCK TABLES `chat_attachments` WRITE;
/*!40000 ALTER TABLE `chat_attachments` DISABLE KEYS */;
/*!40000 ALTER TABLE `chat_attachments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `chat_messages`
--

LOCK TABLES `chat_messages` WRITE;
/*!40000 ALTER TABLE `chat_messages` DISABLE KEYS */;
/*!40000 ALTER TABLE `chat_messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `conditions`
--

LOCK TABLES `conditions` WRITE;
/*!40000 ALTER TABLE `conditions` DISABLE KEYS */;
/*!40000 ALTER TABLE `conditions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `consultation_notes`
--

LOCK TABLES `consultation_notes` WRITE;
/*!40000 ALTER TABLE `consultation_notes` DISABLE KEYS */;
INSERT INTO `consultation_notes` VALUES (1,1,1,1,'Upper respiratory infection','Patient presented with sore throat and fever for 3 days. Prescribed antibiotics.',NULL,0,'2026-03-22 12:51:17'),(2,2,1,1,'overworked,muscle strain','Take at least a week rest .','2026-03-30',0,'2026-03-23 02:12:28'),(3,3,1,1,'overworked,muscle strain','take rest',NULL,0,'2026-03-23 02:16:03'),(4,15,1,1,'overworked,muscle strain','take rest',NULL,0,'2026-03-24 23:43:32');
/*!40000 ALTER TABLE `consultation_notes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `doctor_availability`
--

LOCK TABLES `doctor_availability` WRITE;
/*!40000 ALTER TABLE `doctor_availability` DISABLE KEYS */;
/*!40000 ALTER TABLE `doctor_availability` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `doctors`
--

LOCK TABLES `doctors` WRITE;
/*!40000 ALTER TABLE `doctors` DISABLE KEYS */;
INSERT INTO `doctors` VALUES (1,'Dr. Abin Sharma','Cardiology','abin@clinic.com','$2b$12$871wOVWNNjmnE.m4LnxlYOdWmKiI2WPtsYXTLAyuxaRGIGCLdst96','0420652811','Dr. Abin Sharma has 8 years of experience in Internal Medicine.',1,'doctor','2026-03-22 12:34:10'),(2,'Sijan Budhathoki','Dermatology','sijan@clinic.com','$2b$12$ggPFlncH.lzNPI7GVr0xgubvAyw8RLF80hoitNQI3yoFEjurV7b3y','0406017844','Sijan Budhathoki is a General Practice doctor specialising in primary healthcare and patient wellness.',1,'doctor','2026-03-23 12:37:39'),(3,'Anisha Baniya','Psychiatry','anisha@clinic.com','$2b$12$juNA9j5ybXykJGMpk9XlOOdypXMPjTTEJDA.rETKl8c6u3IZlpjda','0413898054','Anisha Baniya is a General Practice doctor with expertise in appointment management and patient care.',1,'doctor','2026-03-23 12:37:39'),(4,'Nishan Bhattarai','Orthopaedics','nishan.doctor@clinic.com','$2b$12$0u7Ca2MiFDzNYfSaoxC50Oll3sjUbw/LSI2T/5dFz1jmCVlxEJQ3m','0478456301','Nishan Bhattarai is a General Practice doctor specialising in AI-assisted healthcare and digital medicine.',1,'doctor','2026-03-23 12:37:39');
/*!40000 ALTER TABLE `doctors` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `email_logs`
--

LOCK TABLES `email_logs` WRITE;
/*!40000 ALTER TABLE `email_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `email_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `password_reset_tokens`
--

LOCK TABLES `password_reset_tokens` WRITE;
/*!40000 ALTER TABLE `password_reset_tokens` DISABLE KEYS */;
/*!40000 ALTER TABLE `password_reset_tokens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `patient_profiles`
--

LOCK TABLES `patient_profiles` WRITE;
/*!40000 ALTER TABLE `patient_profiles` DISABLE KEYS */;
INSERT INTO `patient_profiles` VALUES (1,1,NULL,NULL,NULL,'2026-03-22 01:10:01'),(2,2,NULL,NULL,NULL,'2026-03-22 13:30:23'),(3,3,NULL,NULL,NULL,'2026-03-25 00:10:37');
/*!40000 ALTER TABLE `patient_profiles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `patients`
--

LOCK TABLES `patients` WRITE;
/*!40000 ALTER TABLE `patients` DISABLE KEYS */;
INSERT INTO `patients` VALUES (1,'Nishan Bhattarai','2004-03-03','nishanbhattarai6789@gmail.com','0478456301','$2b$12$331Yh6hfH1V9KPspRCCDvuP6QOpdjWJ7Tl3PVHR7dcqfDFXnrWbk6',1,1,0,'patient','2026-03-22 01:10:01'),(2,'Amit pandey','2026-03-17','amit.pandey.vu@gmail.com','0478456301','$2b$12$8IAUPB.ItFscngwEeqSdK.Eh/9N8M3S9Uyt51nYO7.zsukgZje.KS',1,1,0,'patient','2026-03-22 13:30:23'),(3,'Nishan Bhattarai','2004-04-23','nishanbhattarai8848@gmail.com','0478456301','$2b$12$z7f.x9HFKybUr7Fvb9IwT.Ug5D3SV9zDhxbJUjikLIXYOQq28JX3O',1,1,0,'patient','2026-03-25 00:10:37');
/*!40000 ALTER TABLE `patients` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `prescriptions`
--

LOCK TABLES `prescriptions` WRITE;
/*!40000 ALTER TABLE `prescriptions` DISABLE KEYS */;
/*!40000 ALTER TABLE `prescriptions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `symptom_logs`
--

LOCK TABLES `symptom_logs` WRITE;
/*!40000 ALTER TABLE `symptom_logs` DISABLE KEYS */;
INSERT INTO `symptom_logs` VALUES (1,1,'internal_itching, itching','[{\"condition\": \"Peptic ulcer diseae\", \"confidence\": 32.6, \"specialist\": \"General Practice\"}, {\"condition\": \"Drug Reaction\", \"confidence\": 3.6, \"specialist\": \"General Practice\"}, {\"condition\": \"Fungal infection\", \"confidence\": 3.0, \"specialist\": \"General Practice\"}, {\"condition\": \"Heart attack\", \"confidence\": 2.4, \"specialist\": \"Cardiology\"}, {\"condition\": \"Chronic cholestasis\", \"confidence\": 2.3, \"specialist\": \"General Practice\"}]','Low',0,'2026-03-22 13:16:01'),(2,1,'fatigue','[{\"condition\": \"Heart attack\", \"confidence\": 3.8, \"specialist\": \"Cardiology\"}, {\"condition\": \"Gastroenteritis\", \"confidence\": 3.5, \"specialist\": \"General Practice\"}, {\"condition\": \"Acne\", \"confidence\": 3.4, \"specialist\": \"Dermatology\"}, {\"condition\": \"AIDS\", \"confidence\": 3.3, \"specialist\": \"General Practice\"}, {\"condition\": \"Allergy\", \"confidence\": 3.3, \"specialist\": \"General Practice\"}]','High',0,'2026-03-22 13:18:28'),(3,1,'fatigue','[{\"condition\": \"Heart attack\", \"confidence\": 3.8, \"specialist\": \"Cardiology\"}, {\"condition\": \"Gastroenteritis\", \"confidence\": 3.5, \"specialist\": \"General Practice\"}, {\"condition\": \"Acne\", \"confidence\": 3.4, \"specialist\": \"Dermatology\"}, {\"condition\": \"AIDS\", \"confidence\": 3.3, \"specialist\": \"General Practice\"}, {\"condition\": \"Allergy\", \"confidence\": 3.3, \"specialist\": \"General Practice\"}]','High',0,'2026-03-22 13:21:08'),(4,1,'skin_rash','[{\"condition\": \"Acne\", \"confidence\": 5.3, \"specialist\": \"Dermatology\"}, {\"condition\": \"Drug Reaction\", \"confidence\": 3.8, \"specialist\": \"General Practice\"}, {\"condition\": \"Heart attack\", \"confidence\": 3.7, \"specialist\": \"Cardiology\"}, {\"condition\": \"Gastroenteritis\", \"confidence\": 3.3, \"specialist\": \"General Practice\"}, {\"condition\": \"AIDS\", \"confidence\": 3.2, \"specialist\": \"General Practice\"}]','Low',0,'2026-03-22 13:21:33'),(5,1,'fatigue','[{\"condition\": \"Heart attack\", \"confidence\": 3.8, \"specialist\": \"Cardiology\"}, {\"condition\": \"Gastroenteritis\", \"confidence\": 3.5, \"specialist\": \"General Practice\"}, {\"condition\": \"Acne\", \"confidence\": 3.4, \"specialist\": \"Dermatology\"}, {\"condition\": \"AIDS\", \"confidence\": 3.3, \"specialist\": \"General Practice\"}, {\"condition\": \"Allergy\", \"confidence\": 3.3, \"specialist\": \"General Practice\"}]','High',0,'2026-03-22 13:26:51'),(6,1,'chest_pain','[{\"condition\": \"GERD\", \"confidence\": 4.7, \"specialist\": \"General Practice\"}, {\"condition\": \"Heart attack\", \"confidence\": 4.7, \"specialist\": \"Cardiology\"}, {\"condition\": \"Gastroenteritis\", \"confidence\": 3.4, \"specialist\": \"General Practice\"}, {\"condition\": \"Acne\", \"confidence\": 3.3, \"specialist\": \"Dermatology\"}, {\"condition\": \"AIDS\", \"confidence\": 3.2, \"specialist\": \"General Practice\"}]','High',0,'2026-03-22 13:27:19'),(7,1,'chest_pain, cough, dizziness, fatigue, chest_pain','[{\"condition\": \"Heart attack\", \"confidence\": 4.6, \"specialist\": \"Cardiology\"}, {\"condition\": \"GERD\", \"confidence\": 4.2, \"specialist\": \"General Practice\"}, {\"condition\": \"Pneumonia\", \"confidence\": 4.0, \"specialist\": \"General Practice\"}, {\"condition\": \"Bronchial Asthma\", \"confidence\": 3.5, \"specialist\": \"General Practice\"}, {\"condition\": \"Hypertension \", \"confidence\": 3.4, \"specialist\": \"General Practice\"}]','High',0,'2026-03-22 13:27:52'),(8,1,'headache, body_ache','[{\"condition\": \"Heart attack\", \"confidence\": 3.8, \"specialist\": \"Cardiology\"}, {\"condition\": \"Gastroenteritis\", \"confidence\": 3.5, \"specialist\": \"General Practice\"}, {\"condition\": \"Acne\", \"confidence\": 3.4, \"specialist\": \"Dermatology\"}, {\"condition\": \"AIDS\", \"confidence\": 3.3, \"specialist\": \"General Practice\"}, {\"condition\": \"Allergy\", \"confidence\": 3.3, \"specialist\": \"General Practice\"}]','High',0,'2026-03-23 02:08:56'),(9,1,'abdominal_pain, acidity','[{\"condition\": \"GERD\", \"confidence\": 4.5, \"specialist\": \"General Practice\"}, {\"condition\": \"Chronic cholestasis\", \"confidence\": 4.4, \"specialist\": \"General Practice\"}, {\"condition\": \"Hepatitis D\", \"confidence\": 3.5, \"specialist\": \"General Practice\"}, {\"condition\": \"Heart attack\", \"confidence\": 3.4, \"specialist\": \"Cardiology\"}, {\"condition\": \"Jaundice\", \"confidence\": 3.2, \"specialist\": \"General Practice\"}]','Low',0,'2026-03-23 02:13:32'),(10,1,'abdominal_pain, acidity','[{\"condition\": \"GERD\", \"confidence\": 4.5, \"specialist\": \"General Practice\"}, {\"condition\": \"Chronic cholestasis\", \"confidence\": 4.4, \"specialist\": \"General Practice\"}, {\"condition\": \"Hepatitis D\", \"confidence\": 3.5, \"specialist\": \"General Practice\"}, {\"condition\": \"Heart attack\", \"confidence\": 3.4, \"specialist\": \"Cardiology\"}, {\"condition\": \"Jaundice\", \"confidence\": 3.2, \"specialist\": \"General Practice\"}]','Low',0,'2026-03-23 02:14:18'),(11,1,'blackheads, blister','[{\"condition\": \"Impetigo\", \"confidence\": 17.2, \"specialist\": \"Dermatology\"}, {\"condition\": \"Acne\", \"confidence\": 7.8, \"specialist\": \"Dermatology\"}, {\"condition\": \"Heart attack\", \"confidence\": 3.0, \"specialist\": \"Cardiology\"}, {\"condition\": \"Gastroenteritis\", \"confidence\": 2.8, \"specialist\": \"General Practice\"}, {\"condition\": \"Drug Reaction\", \"confidence\": 2.7, \"specialist\": \"General Practice\"}]','Low',0,'2026-03-23 03:38:12');
/*!40000 ALTER TABLE `symptom_logs` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-08 22:47:20
