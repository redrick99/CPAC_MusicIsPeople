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

int cols, rows;
int scl = 8;
// Change the dimension of the terrain
int w = 1025;
int h = 900;

float flying = 0;

float[][] terrain;
float[] amplitude = new float[1025];

PImage logo;
float logoLength = 975;
float logoHeight = 100;
float rumor;
int count=0;
Boolean active = false;

float xOff = 0;
float yOff = 0;
float xInc = 0.02;
float yInc = 0.02;
float scale = 100;
int numDots = 3;         // Number of dots to display
int dotSize = 20;        // Size of the dots
int dotSpacing = 50;     // Spacing between the dots
int dotColor = color(255, 255, 255);  // Color of the dots
int textColor = color(255);           // Color of the loading text
int textSize = 50;       // Size of the loading text

void setup() {
  size(1500, 900, P3D);
  myClient = new Client(this, "127.0.0.1", 54321);
  activeClient = new Client(this, "127.0.0.1", 13524);
  surface.setResizable(true);

  cols = w /scl;
  rows = h / scl;
  terrain = new float[cols][rows];
  logo = loadImage("./GUI_resources/LogoMIP-iPad.jpg");

  Line.Info lineInfo = new Line.Info(SourceDataLine.class);
  Line line = null;
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
  if(active){
    loadingDone();
    mainPage();
  }
  else{
    loadingDone();
    loadingPage();
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
      active = true;
    }
    if(inputString.equals("STOP")){
      active = false;
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
    image(logo, width/2 - logoLength/2, 50, logoLength, logoHeight);
    stroke(255);
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

void loadingPage(){

  background(BACKGROUND);

  // Loop through all pixels in the window
  loadPixels();
  for (int x = 0; x < width; x++) {
    for (int y = 0; y < height; y++) {

      // Calculate the noise value for this pixel
      float noiseVal = noise(xOff*x*xInc, yOff*y*yInc);
      noiseVal = pow(noiseVal, 1);  // Adjust the noise curve

      // Map the noise value to a color and set the pixel color
      float colorVal = map(noiseVal, 0, 1, 0, 255);
      int pixelColor = color(
        map(colorVal, 0, 255, 0, 170),
        map(colorVal, 0, 255, 0, 190),
        map(colorVal, 0, 255, 0, 108)
      );
      pixels[x + y * width] = pixelColor;
    }
  }
  updatePixels();

  // Increment the noise offset values to move the noise over time
  xOff += 0.01;
  yOff += 0.01;

  // Draw the loading text
  image(logo, width/2 - logoLength/2, 50, logoLength, logoHeight);
  fill(textColor);
  textSize(textSize);
  textAlign(CENTER, CENTER);
  text("Loading", width/2, height/2 - dotSpacing);

  // Draw the dots
    for (int i = 0; i < numDots; i++) {
      int dotX = width/2 - (numDots-1)*dotSpacing/2 + i*dotSpacing;
      fill(dotColor);
      ellipse(dotX, height/2 + dotSpacing, dotSize, dotSize);
    }
}