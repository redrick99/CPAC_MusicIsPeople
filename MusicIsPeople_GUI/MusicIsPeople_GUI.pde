import processing.net.*;
import java.util.Scanner;
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


int cols, rows;
int scl = 20;
// Change the dimension of the terrain
int w = 1025;
int h = 900;

float flying = 0;

float[][] terrain;
float[] amplitude = new float[1025];

PImage logo;
float logoLength = 600;
float logoHeight = 150;
float rumor;
int count=0;

void setup() {
  size(1500, 900, P3D);
  myClient = new Client(this, "127.0.0.1", 54321);
  surface.setResizable(true);
  frameRate(500);

  cols = w /scl;
  rows = h / scl;
  terrain = new float[cols][rows];
  logo = loadImage("./resources/logoMIP.png");
}

void draw(){
  count += 1;
  count = count%(h/scl);
  flying -= 0.001;

  // myClient.available() returns the number of bytes stored in the buffer
  if(myClient.available() > 0){
    receiveMessageHandler(myClient.readString());
  }




  float[] values = new float[2200];
  for(int i = 0; i < w; i++){
    values[i] = i/10; // MODIFY THIS: THESE ARE THE VALUES THAT WILL BE MOLTIPLIED BY THE NOISE ARRAY
  }

  createMesh();

  background(BACKGROUND);
  image(logo, width/2 - logoLength/2, 0, logoLength, logoHeight);
  stroke(255);
  noFill();

  // Create the structure of the "ocean"
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
  println(stringArray.length);
  for (int i = 0; i < 20; i++) {
    amplitude[i] = float(stringArray[i]); // convert each string to a float and store it in the array
  }
}

// Create the background perlin noise
void createMesh(){
  float yoff=flying;
    for(int y = 1; y < rows; y++){
    float xoff = 0;
    for(int x=1; x<cols; x++){
      // the noise function returns value from 0.0 to 1.0, the map function
      // maps these values in another scale
      rumor = noise(xoff, yoff);
      terrain[x][y] = map(rumor, 0, 1, -500*amplitude[x]-20, 500*amplitude[x]+20); // Change the amplitude of the wave
      terrain[x-1][y-1] = terrain[x][y];
      xoff +=0.1;
    }
    yoff+=0.1;
  }

}

/*
void createMesh(){
  float yoff=flying;
    for(int y = 0; y < rows; y++){
    float xoff = 0;
    for(int x=0; x<cols; x++){
      float noiseVal = customNoise(xoff, yoff, amplitude);
      terrain[x][y] = map(noiseVal, 0, 1, -50, 50); // Change the amplitude of the wave
      xoff +=0.1;
    }
    yoff+=0.1;
  }
}

float customNoise(float xoff, float yoff, float[] amplitude){
  float noiseVal = 0;
  float frequency = 0.05;
  float amplitudeSum = 0;
  for(int i = 0; i < amplitude.length; i++){
    amplitudeSum += amplitude[i];
    noiseVal += amplitude[i] * noise(xoff * frequency, yoff * frequency);
    frequency *= 2.0;
  }
  noiseVal /= amplitudeSum;
  return noiseVal;
}
*/