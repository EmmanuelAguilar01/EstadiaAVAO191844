-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 07-03-2025 a las 03:01:00
-- Versión del servidor: 10.4.22-MariaDB
-- Versión de PHP: 8.1.0

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `detector`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `dataexperiment`
--

CREATE TABLE `dataexperiment` (
  `idDataSetExp` int(11) NOT NULL,
  `idUsuarios` int(11) NOT NULL,
  `idTiposBasura` int(11) NOT NULL,
  `NombreDataExp` varchar(15) NOT NULL,
  `FormatoExp` varchar(5) NOT NULL,
  `Imagenes` int(11) NOT NULL,
  `Tecnologia` varchar(15) NOT NULL,
  `Ruta` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `datasetprueba`
--

CREATE TABLE `datasetprueba` (
  `idDataSetPrueba` int(11) NOT NULL,
  `idUsuarios` int(11) NOT NULL,
  `idTiposBasura` int(11) NOT NULL,
  `NombreData` varchar(15) NOT NULL,
  `Formato` varchar(5) NOT NULL,
  `Cantidad` int(11) NOT NULL,
  `Ruta` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `evaluacion`
--

CREATE TABLE `evaluacion` (
  `idEvaluacion` int(11) NOT NULL,
  `idDataSetPrueba` int(4) NOT NULL,
  `NombreEvaluacion` varchar(20) NOT NULL,
  `TiempoMinYOLO` time NOT NULL,
  `ErrorYOLO` float NOT NULL,
  `PrecisionYOLO` float NOT NULL,
  `SensibilidadYOLO` float NOT NULL,
  `EspecifidadYOLO` float NOT NULL,
  `TiempoMinDETR` time NOT NULL,
  `ErrorDETR` float NOT NULL,
  `PrecisionDETR` float NOT NULL,
  `SensibilidadDETR` float NOT NULL,
  `EspecifidadDETR` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `experimentador`
--

CREATE TABLE `experimentador` (
  `idExperimentador` int(11) NOT NULL,
  `idUsuarios` int(11) NOT NULL,
  `idDataSetExp` int(11) NOT NULL,
  `NombreModelo` varchar(20) NOT NULL,
  `Arquitectura` varchar(20) NOT NULL,
  `PorcentajeErr` float NOT NULL,
  `Precision` float NOT NULL,
  `TiempoHoras` time NOT NULL,
  `Pesos` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tiposbasura`
--

CREATE TABLE `tiposbasura` (
  `idTiposBasura` int(11) NOT NULL,
  `TipoBasura` varchar(20) NOT NULL,
  `Descrip` varchar(50) NOT NULL,
  `Afectaciones` varchar(50) NOT NULL,
  `TiempoDegradacion` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Volcado de datos para la tabla `tiposbasura`
--

INSERT INTO `tiposbasura` (`idTiposBasura`, `TipoBasura`, `Descrip`, `Afectaciones`, `TiempoDegradacion`) VALUES
(1, 'Plástico PET', 'Botellas PET reciclables', 'Contaminación marina y terrestre', 450),
(9, 'Residuos Electrónico', 'Celulares, computadoras y electrodomésticos', 'Metales pesados, contaminación del suelo', 1200),
(10, 'Desechos Orgánicos', 'Restos de comida y desechos vegetales', 'Emisión de metano, proliferación de plagas', 0),
(15, 'Bolsas plásticas', 'Bolsas de supermercado', 'Bloqueo de desagües, afecta fauna', 300),
(16, 'Latas de aluminio', 'Latas de bebidas y conservas', 'Contaminación por metales', 400),
(17, 'Vidrio', 'Botellas y frascos de vidrio', 'Puede causar incendios', 4000),
(18, 'Pilas y baterías', 'Pilas comunes y recargables', 'Metales pesados, contaminación de agua', 700),
(19, 'Colillas de cigarro', 'Filtros de cigarro', 'Contaminación del agua y suelos', 5),
(20, 'Cartón y papel', 'Cajas de cartón y papel', 'Desperdicio de recursos', 1),
(21, 'Aceites usados', 'Aceites de cocina y motor', 'Contaminación del agua', 1000);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `idUsuarios` int(11) NOT NULL,
  `Nombre` varchar(50) NOT NULL,
  `Apellido` varchar(40) NOT NULL,
  `Correo` varchar(50) NOT NULL,
  `Contra` varchar(255) NOT NULL,
  `Tipo` varchar(20) NOT NULL,
  `FechaRegistro` date NOT NULL,
  `Intereses` varchar(100) NOT NULL,
  `Procedencia` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`idUsuarios`, `Nombre`, `Apellido`, `Correo`, `Contra`, `Tipo`, `FechaRegistro`, `Intereses`, `Procedencia`) VALUES
(1, 'Emmanuel', 'Aguilar', 'emmanuel.agva@gmail.com', 'pbkdf2:sha256:260000$6sriSZJ9pbZWkdQB$a0da53c3c312549f044607e55a6983fcb52811366b14709699e9e36f86c101c9', 'Administrador', '2024-07-02', 'Conocer sobre modelos de deteccion', 'Upemor'),
(42, 'Antonio', 'Bustos', 'r-emmanuel_n@hotmail.com', 'pbkdf2:sha256:260000$26X2VhduUWASxc6w$e905c67c8905cd8d536099939e76433464d8e6af5d5580d5f70a4d147a69432a', 'Tester', '2024-09-10', 'Practicar', 'Upemore'),
(43, 'Sandra', 'Yadira', 'negociosagva@gmail.com', 'pbkdf2:sha256:260000$NquEK5s6Pe0yHZfK$dfd6437ff763e14d3d15d6726fa495219af1136787a081a1d5a4dfe10abc0bfc', 'Administrador', '2024-11-15', 'Ayudar', 'FrayLucca');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `dataexperiment`
--
ALTER TABLE `dataexperiment`
  ADD PRIMARY KEY (`idDataSetExp`),
  ADD KEY `idUsuarios` (`idUsuarios`),
  ADD KEY `idTiposBasura` (`idTiposBasura`);

--
-- Indices de la tabla `datasetprueba`
--
ALTER TABLE `datasetprueba`
  ADD PRIMARY KEY (`idDataSetPrueba`,`idUsuarios`),
  ADD KEY `idUsuarios` (`idUsuarios`),
  ADD KEY `idTiposBasura` (`idTiposBasura`);

--
-- Indices de la tabla `evaluacion`
--
ALTER TABLE `evaluacion`
  ADD PRIMARY KEY (`idEvaluacion`,`idDataSetPrueba`),
  ADD KEY `evaluacion_ibfk_1` (`idDataSetPrueba`);

--
-- Indices de la tabla `experimentador`
--
ALTER TABLE `experimentador`
  ADD PRIMARY KEY (`idExperimentador`,`idUsuarios`),
  ADD KEY `idUsuarios` (`idUsuarios`),
  ADD KEY `idDataSetExp` (`idDataSetExp`);

--
-- Indices de la tabla `tiposbasura`
--
ALTER TABLE `tiposbasura`
  ADD PRIMARY KEY (`idTiposBasura`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`idUsuarios`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `dataexperiment`
--
ALTER TABLE `dataexperiment`
  MODIFY `idDataSetExp` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `datasetprueba`
--
ALTER TABLE `datasetprueba`
  MODIFY `idDataSetPrueba` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `evaluacion`
--
ALTER TABLE `evaluacion`
  MODIFY `idEvaluacion` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `experimentador`
--
ALTER TABLE `experimentador`
  MODIFY `idExperimentador` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `tiposbasura`
--
ALTER TABLE `tiposbasura`
  MODIFY `idTiposBasura` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `idUsuarios` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=47;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `dataexperiment`
--
ALTER TABLE `dataexperiment`
  ADD CONSTRAINT `dataexperiment_ibfk_1` FOREIGN KEY (`idUsuarios`) REFERENCES `usuarios` (`idUsuarios`),
  ADD CONSTRAINT `dataexperiment_ibfk_2` FOREIGN KEY (`idTiposBasura`) REFERENCES `tiposbasura` (`idTiposBasura`);

--
-- Filtros para la tabla `datasetprueba`
--
ALTER TABLE `datasetprueba`
  ADD CONSTRAINT `datasetprueba_ibfk_1` FOREIGN KEY (`idUsuarios`) REFERENCES `usuarios` (`idUsuarios`),
  ADD CONSTRAINT `datasetprueba_ibfk_2` FOREIGN KEY (`idTiposBasura`) REFERENCES `tiposbasura` (`idTiposBasura`);

--
-- Filtros para la tabla `evaluacion`
--
ALTER TABLE `evaluacion`
  ADD CONSTRAINT `evaluacion_ibfk_1` FOREIGN KEY (`idDataSetPrueba`) REFERENCES `datasetprueba` (`idDataSetPrueba`) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Filtros para la tabla `experimentador`
--
ALTER TABLE `experimentador`
  ADD CONSTRAINT `experimentador_ibfk_1` FOREIGN KEY (`idUsuarios`) REFERENCES `usuarios` (`idUsuarios`),
  ADD CONSTRAINT `experimentador_ibfk_2` FOREIGN KEY (`idDataSetExp`) REFERENCES `dataexperiment` (`idDataSetExp`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
