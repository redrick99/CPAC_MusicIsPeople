import processing.net.*;
import java.util.Scanner;
import java.util.Arrays;
import javax.sound.sampled.*;
import processing.sound.*;
Client myClient;
Client activeClient;
import com.jogamp.opengl.GLProfile;
{
  GLProfile.initSingleton();
}


FloatControl control;

final color BACKGROUND = #2C302E;
final color BLUE = #75B9BE;
final color YELLOW = #FFF275;
final color GREEN = #457604;
final color RED = #FF5C5C;
final color GRAY = #212E2F;
final color AZURE = #84B7BD;
final color LAVENDER = #E6E6FA;

int cols, rows;
int scl = 8;

// Change the dimension of the terrain
int w = 1025;
int h = 900;

float flying = 0;

float[][] terrain;
float[] amplitude = new float[1025];

float logoLength = 975;
float logoHeight = 100;
float rumor;
int count=1;
int active = 1;

float xOff = 0;
float yOff = 0;
float xInc = 0.02;
float yInc = 0.02;
float scale = 100;
int numLines = 25;         // Number of dots to display
int dotSize = 20;        // Size of the dots
int dotSpacing = 10;     // Spacing between the dots
int dotColor = color(AZURE);  // Color of the dots
int textColor = color(255);           // Color of the loading text
int textSize = 50;       // Size of the loading text
float base = 5;  // Set the base of the rectangle
float yH = 20;  // Set the height of the rectangle
PFont font;

ArrayList<Sentence> database;
int phraseIndex = 0;
int prevIndex;

Boolean ctrl = true;
int dTime;
float startAngle = -HALF_PI;
float endAngle = 0;
int startTime;
int duration = 7000;

void setup() {
  size(1500, 900, P3D);
  myClient = new Client(this, "127.0.0.1", 54321);
  activeClient = new Client(this, "127.0.0.1", 13524);
  surface.setResizable(true);
  
  font = createFont("Monospaced", 50);

  cols = w /scl;
  rows = h / scl;
  terrain = new float[cols][rows];
  Line.Info lineInfo = new Line.Info(SourceDataLine.class);
  Line line = null;
  database = Sentence.createSentenceDatabase();
  try {
    line = AudioSystem.getLine(lineInfo);
    line.open();

    // Get the volume control for the line
    control = (FloatControl) line.getControl(FloatControl.Type.MASTER_GAIN);
  } catch (LineUnavailableException ex) {
    ex.printStackTrace();
  }
}

void draw(){
  loadingDone();
  if(active == 2){
    mainPage();
  }
  else if(active == 1){
    if(ctrl){
      prevIndex = phraseIndex;
      phraseIndex = floor(random(database.size()));
      while(prevIndex == phraseIndex) phraseIndex = floor(random(database.size()));
      ctrl = false;
      dTime = millis();
    }
    if(millis() - dTime >= duration){
      ctrl = true;
    }
     buildingPage();
   }
   else{
     loadingPage();
     ctrl = true;
   }
}

// Reader of the messages from the server
void receiveMessageHandler(String fromServerMessage) {
  String inputString = fromServerMessage; // input string containing float values
  inputString = inputString.replaceAll("\\[|\\]|\\s", ""); // remove square brackets and spaces
  String[] stringArray = inputString.split(","); // split the string into an array of strings
  for (int i = 0; i < amplitude.length-1; i++) {
    amplitude[i] = float(stringArray[i]); // convert each string to a float and store it in the array
  }
}
// Function to shift each line backwards
void propagate(){
  for(int y = rows-1; y > 0; y--) {
    for(int x = 0; x < cols; x++) {
      terrain[x][y] = terrain[x][y-1];
    }
  }
}

// Get the info about the current level of the volume of the computer
float getSystemVolume() {
  Mixer.Info[] mixerInfo = AudioSystem.getMixerInfo();
  for (Mixer.Info info : mixerInfo) {
    Mixer mixer = AudioSystem.getMixer(info);
    if (mixer.isLineSupported(Port.Info.SPEAKER)) {
      try {
        mixer.open();
        Port port = (Port)mixer.getLine(Port.Info.SPEAKER);
        port.open();
        FloatControl volumeControl = (FloatControl)port.getControl(FloatControl.Type.VOLUME);
        float volume = volumeControl.getValue() / volumeControl.getMaximum();
        port.close();
        mixer.close();
        return volume;
      } catch (LineUnavailableException ex) {
        ex.printStackTrace();
      } catch (Exception e){
        return 1.0;
      }
    }
  }
  return 0;
}

void loadingDone(){
  if(activeClient.available()>0){
    String inputString = activeClient.readString(); // input string containing float values
    println("LOADING...");
    println(inputString);
    if(inputString.equals("START")){
      active = 2;
    }
    if(inputString.equals("CREATING")){
      active = 1;
    }
    if(inputString.equals("STOP")){
      active = 0;
    }
  }
}

void mainPage(){
  // Get the current volume level as a float value between 0.0 and 1.0
    float volume = getSystemVolume();

    // Define the speed of the propagation, is update every time the function draw() is called
    flying -= 0.05;

    // If the client is not writing anything on the buffer it is not necessary to read from it
    if(myClient.available() > 0){
      receiveMessageHandler(myClient.readString());
    }
    // Define the amplitude of the waveform
    for(int i = 0; i < cols; i++){
        terrain[i][0] = 500*volume*amplitude[i];
        terrain[i][0] += 10*sin(flying);
    }

    propagate();

    background(BACKGROUND);
    fill(YELLOW, 70);
    stroke(YELLOW);
    rect(width/2 - logoLength/2, 50, logoLength, logoHeight);
    
    
    textSize(textSize);
    textAlign(CENTER, CENTER);
    textFont(font);
    fill(YELLOW);
    text("Music Is People", width/2 - logoLength/2, 50, logoLength, logoHeight);    stroke(255);
    noFill();

    // Create the blue structure
    translate(width/2, height/2);
    rotateX(PI/3);
    translate(-w/2, -h/7);                               // Change the position of the terrain
    for(int y = 0; y < rows-1; y++){
      beginShape(TRIANGLE_STRIP);
      for(int x=0; x<cols; x++){
        fill(BLUE);
        vertex(x*scl, y*scl, terrain[x][y]);
        vertex(x*scl, (y+1)*scl, terrain[x][y+1]);
      }
      endShape();
    }
}

void loadingPage() {
  background(BACKGROUND);
  fill(BACKGROUND);
  stroke(AZURE);
  rect(width/2 - (numLines-1)*dotSpacing/2, height/2 + 3*dotSpacing, (numLines-1)*dotSpacing, 6*dotSpacing + yH);

  // Draw the logo
  fill(YELLOW, 70);
  stroke(YELLOW);
  rect(width/2 - logoLength/2, 50, logoLength, logoHeight);
  textSize(textSize);
  textAlign(CENTER, CENTER);
  textFont(font);
  fill(YELLOW);
  text("Music Is People", width/2 - logoLength/2, 50, logoLength, logoHeight);
  
  // Draw the loading text
  fill(AZURE);
  textSize(30);
  text("...loading...", width/2, height/2 - dotSpacing);

  // Calculate the base opacity for fade-in fade-out effect
  int baseOpacity = 200;

  // Calculate the animation parameters
  float phaseOffset = 0.02;
  float light = 200.0;

  // Draw the lines
  for (int i = 0; i < numLines; i++) {
    int dotX = width/2 - (numLines-1)*dotSpacing/2 + i*dotSpacing;
    float phase = -phaseOffset * dotX;
    int opacity = int(baseOpacity + sin(phase + frameCount * 0.05) * light);

    // Set the color and opacity for the line
    stroke(AZURE, opacity);
    
    // Draw the line
    line(dotX, height/2 + 5*dotSpacing, dotX, height/2 + 7*dotSpacing + yH);
  }
}

void buildingPage() {
    background(BACKGROUND);
    fill(BACKGROUND);
    stroke(LAVENDER);
    rect(width/2 - (numLines-1)*dotSpacing/2, height/2 + 3*dotSpacing, (numLines-1)*dotSpacing, 6*dotSpacing + yH);

    // Draw the logo
    fill(YELLOW, 70);
    stroke(YELLOW);
    rect(width/2 - logoLength/2, 50, logoLength, logoHeight);
    textSize(textSize);
    textAlign(CENTER, CENTER);
    textFont(font);
    fill(YELLOW);
    text("Music Is People", width/2 - logoLength/2, 50, logoLength, logoHeight);

    // Draw the loading text
    fill(LAVENDER);
    textSize(30);
    text("...creating...", width/2, height/2 - dotSpacing);

    // Calculate the base opacity for fade-in fade-out effect
    // int baseOpacity = 200;

    // Calculate the animation parameters
    // float phaseOffset = 0.02;
    // float light = 200.0;

    // Calculate the stretch parameters
    float stretchAmount = 15.0; // Adjust the stretch amount here

    // Draw the lines
    for (int i = 0; i < numLines; i++) {
        int dotX = width/2 - (numLines-1)*dotSpacing/2 + i*dotSpacing;
        // float phase = -phaseOffset * dotX;
        // int opacity = int(baseOpacity + sin(phase + frameCount * 0.05) * light);

        // Set the color and opacity for the line
        stroke(LAVENDER);

        // Calculate the line coordinates
        float startY = height/2 + 5*dotSpacing;
        float endY = height/2 + 7*dotSpacing + yH;
        
        // Calculate the stretched end position based on the dotX
        float stretchedEndY = endY + (sin((frameCount - dotX) * 0.05) * stretchAmount);
        float stretchedStartY = startY + (sin((frameCount - dotX) * 0.05) * stretchAmount);
        
        // Draw the line
        line(dotX, stretchedStartY, dotX, stretchedEndY);
    }
    
    // Draw the loading text
    fill(255);
    textSize(20);
   

    if(database.get(phraseIndex).text.length() > 100){
      int index = 100;
      for(index = 100; index < database.get(phraseIndex).text.length(); index++){
        if(database.get(phraseIndex).text.charAt(index) == ' ') break;
      }
      text(database.get(phraseIndex).text.substring(0, index), width/2, height/2 + height/3);
      text(database.get(phraseIndex).text.substring(index), width/2, height/2 + height/3 + 50);
    }
    else text(database.get(phraseIndex).text, width/2, height/2 + height/3);
     
    draw_circle();
}

void draw_circle(){
  int elapsedTime = millis() - dTime;
  
  // Calculate the start and end angles of the circular crown based on elapsed time
  startAngle = -HALF_PI;
  endAngle = map(elapsedTime, 0, duration, startAngle, TWO_PI-HALF_PI);
  
  // Set up the circular crown properties
  fill(LAVENDER, 80);
  noStroke();
  translate(width/2, height/2 + height/4);
  
  
  // Draw the circular crown
  float crownSize = 40;
  float crownRadius = crownSize*0.8;
  arc(0, 0, crownSize, crownSize, startAngle, endAngle, PIE);
  fill(BACKGROUND);
  arc(0, 0, crownRadius, crownRadius, startAngle, endAngle, PIE);
  
  // Check if the loading is complete
  if (elapsedTime >= duration) {
    // Reset the start time
    startTime = millis();
  }
}
