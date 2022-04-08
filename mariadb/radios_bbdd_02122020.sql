-- phpMyAdmin SQL Dump
-- version 5.0.2
-- https://www.phpmyadmin.net/
--
-- Servidor: bbdd
-- Tiempo de generación: 02-12-2020 a las 12:29:26
-- Versión del servidor: 10.4.13-MariaDB-1:10.4.13+maria~focal
-- Versión de PHP: 7.4.9

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `radios`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `radios`
--

CREATE TABLE `radios` (
  `id` int(255) NOT NULL,
  `ServiceName` varchar(100) NOT NULL,
  `InputUrl` varchar(100) NOT NULL,
  `Outputs` int(10) NOT NULL,
  `OutputFormat` varchar(10) NOT NULL,
  `AudioCodec` varchar(10) NOT NULL,
  `AudioBitrate` varchar(20) NOT NULL,
  `AudioRate` varchar(20) NOT NULL,
  `AudioProfile` varchar(10) NOT NULL DEFAULT '',
  `ServerIp` varchar(100) NOT NULL,
  `ServerPort` varchar(5) NOT NULL,
  `ServerFolder` varchar(255) NOT NULL DEFAULT '',
  `ServerUser` varchar(20) NOT NULL DEFAULT '',
  `ServerPassword` varchar(20) NOT NULL DEFAULT '',
  `Status` tinyint(1) NOT NULL DEFAULT 0,
  `ContainerId` varchar(100) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `radios`
--
ALTER TABLE `radios`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `radios`
--
ALTER TABLE `radios`
  MODIFY `id` int(255) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
