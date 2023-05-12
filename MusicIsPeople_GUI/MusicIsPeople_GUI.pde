import processing.net.*;
import java.util.Scanner;
import java.util.Arrays;
Client myClient;
import com.jogamp.opengl.GLProfile;
{
  GLProfile.initSingleton();
}



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

void setup() {
  size(1500, 900, P3D);
  myClient = new Client(this, "127.0.0.1", 54321);
  surface.setResizable(true);

  cols = w /scl;
  rows = h / scl;
  terrain = new float[cols][rows];
  logo = loadImage("./GUI_resources/LogoMIP-iPad.jpg");
}

void draw(){
  flying -= 0.05;
  
  if(myClient.available() > 0){
    receiveMessageHandler(myClient.readString());
  }
  for(int i = 0; i < cols; i++){
      terrain[i][0] = 500*amplitude[i];
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

void receiveMessageHandler(String fromServerMessage) {
  String inputString = fromServerMessage; // input string containing float values
  inputString = inputString.replaceAll("\\[|\\]|\\s", ""); // remove square brackets and spaces
  String[] stringArray = inputString.split(","); // split the string into an array of strings
  for (int i = 0; i < amplitude.length-1; i++) {
    amplitude[i] = float(stringArray[i]); // convert each string to a float and store it in the array
  }
}

void propagate(){
  for(int y = rows-1; y > 0; y--) {
    for(int x = 0; x < cols; x++) {
      terrain[x][y] = terrain[x][y-1];
    }
  }
}
