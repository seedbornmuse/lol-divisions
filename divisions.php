<html>
<head>
</head>

<body>

<?php
/*
	To anyone who happens to read this: I am ashamed and really need to learn more php.

TODO:
	-REPLACE select_GET by just using variables, its dumb
	-NEED TO STANDARDIZE PARAMETER NAMES,FORMATS( mode, tier, etc)
	-SECURITY
	-standardize single/double quotes on this and python
	-Mixing php and html seems a bit awkward, try to find better way to format?
*/

	function select_GET($param, $value){
		if( isset($_GET[$param]) && $_GET[$param] === $value)
			return "selected";
		return "";
	}

	$modes = array(1 => "RANKED_SOLO_5x5", 2 => "RANKED_TEAM_3x3", 3 => "RANKED_TEAM_5x5");
	$tiers = array(1 => "Bronze", 2 => "Silver", 3 => "Gold", 4 => "Platinum", 5 => "Diamond");
	
	$region = isset($_GET["region"]) ? $_GET["region"] : null;
	$mode = isset($_GET["mode"]) ? $_GET["mode"] : null;
	$tier = isset($_GET["tier"]) ? $_GET["tier"] : null;
	$champion = isset($_GET["champion"]) ? $_GET["champion"] : null;

?>
<form>
<!-- RESTRUCTURE THIS SECTION USING LOOP TO ITERATE THROUGH ARRAY/MAP OF OPTIONS -->
	<select name="region">
		<option value="na" selected>NA</option>
		<!--<option value="EU">EU</option>-->
	</select>
	<select name="mode">
	<?php
		foreach( $modes as $value ) {
			$selected = ' ' . select_GET("mode",$value);
			//echo '<option value="' . $value . '"' . $selected . '>' . $value . '</option>';
			printf( '<option value="%s" %s>%s</option>', $value, $selected, $value);
		
		}
		/*<option value="RANKED_SOLO_5x5">Solo Queue</option>
		<option value="RANKED_TEAM_3x3">Team 3v3</option>
		<option value="RANKED_TEAM_5x5">Team 5v5</option>*/
	?>
	</select>
	<select name="tier">
	<?php
		foreach( $tiers as $value ) {
			$selected = ' ' . select_GET("tier",$value);
			//echo '<option value="' . $value . '"' . $selected . '>' . $value . '</option>';
			printf( '<option value="%s" %s>%s</option>', $value, $selected, $value);
		}
	
		/*<option value="Bronze">Bronze</option>
		<option value="Silver">Silver</option>
		<option value="Gold">Gold</option>
		<option value="Platinum">Platinum</option>
		<option value="Diamond">Diamond</option>
		*/
	?>
	</select>
	<select name="champion">
	<?php
		//Read champions from file list
		//Careful to avoid adding extra line at end of champ list, or could add check to ignore it
		$champfile = fopen("champions.txt", "r");
		while( $champ = trim(fgets($champfile)) ){
			echo "<option value=\"" . $champ . "\">" . $champ . "</option>";
		}
		fclose($champfile);
	?>
	</select>
	<input type="submit" value="Submit">
</form>

<?php
$username = "root";
$password = "mysql";
$hostname = "localhost"; 
$database = "divisions";

 //Index if found, false otherwise
$mode_index = array_search($mode, $modes);
$tier_index = array_search($tier, $tiers);

if ($region != null && $mode_index !== false && $tier_index !== false && $champion != null ){
	$query = "SELECT * FROM " . $region;
	//$query .= " WHERE " . implode(" AND ", array($mode, $tier, $champion));
	$query .= " WHERE " . "mode=" . $mode_index . " AND tier=" . $tier_index . " AND champion='" . $champion . "'";
	echo $query . "<br>";
	
	$mysqli = new mysqli($hostname, $username, $password, $database);

	if ($mysqli->connect_errno) {
		echo "There was an error retrieving data on the server";
		
	} else if ($result = $mysqli->query($query)) {
	
		echo $result->num_rows . " result" . (($result->num_rows > 1) ? 's' : '') . " found<br>";
		
		//$result->data_seek(0);
		while ($row = $result->fetch_assoc()) {
			echo $row['champion'] . "'s " . $row['suffix'] . " - " . $row['members'] . "<br>";
		}

		$result->close();
	}

	$mysqli->close();
	
}


?>

</body>
</html>