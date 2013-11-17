from Tkinter import Frame, Canvas, YES, BOTH
import Leap, sys

class SignatureListener(Leap.Listener):

    state = 0 # default = 0, recording = 1, saving = 2, wait = 3,4, exit = -1
    noin = 0 # counter for frames when no hands in screen
    wait = 0 # wait count
    lastwait = 0
    xcor = []
    ycor = []
    xsav = []
    ysav = []

    def normalize(self, coords):
        offset = coords[0]
        for i in coords:
            i -= offset
        return coords    

    # Signature comparison algorithm (CRUDE)
    def sigcomp(self):
        if (abs(len(self.xcor) - len(self.xsav)) > 0.2 * len(self.xsav)):
            return -1
        if len(self.xcor) > 50:
            self.xcor = self.xcor[20:-10]
            self.ycor = self.ycor[20:-10]
        if len(self.xsav) > 50:
            self.xsav = self.xsav[20:-10]
            self.ysav = self.ysav[20:-10]
        self.xcor = self.normalize(self.xcor)
        self.ycor = self.normalize(self.ycor)
        self.xsav = self.normalize(self.xsav)
        self.ysav = self.normalize(self.ysav)
        diff = 0
        ind = 0
        while (ind < len(self.xcor) and ind < len(self.xsav)):
            diff += abs(self.xcor[ind] - self.xsav[ind])
            ind += 1
        if len(self.xsav) != 0:
            diff /= len(self.xsav)
        return diff

    def on_init(self, controller):
        print "Initialized"

    def on_connect(self, controller):
        print "Connected"
        print "Press [Enter] to initiate recording"

    def on_frame(self, controller):
        #self.paintCanvas.delete("all")
        frame = controller.frame()

        interactionBox = frame.interaction_box
        for pointable in frame.pointables:
            normalizedPosition = interactionBox.normalize_point(pointable.tip_position)
            if(pointable.touch_distance > 0 and pointable.touch_zone != Leap.Pointable.ZONE_NONE):
                color = self.rgb_to_hex((0, 255 - 255 * pointable.touch_distance, 0))

            elif(pointable.touch_distance <= 0):
                color = self.rgb_to_hex((-255 * pointable.touch_distance, 0, 0))
                #color = self.rgb_to_hex((255,0,0))

            else:
                color = self.rgb_to_hex((0,0,200))

            self.draw(normalizedPosition.x * 800, 600 - normalizedPosition.y * 600, 20, 20, color)
        
        if self.state == 0:
            s = sys.stdin.readline()
            if s == "\n":
                self.state = 4
        elif self.state == 1 or self.state == 2: #recording state
            if not frame.hands.is_empty:
                self.noin = 0
                # Get the first hand
                hand = frame.hands[0]

                # Check if the hand has any fingers
                fingers = hand.fingers
                if not fingers.is_empty:
                    # Calculate the hand's average finger tip position
                    if len(fingers) in (1, 2):
                        avg_pos = Leap.Vector()
                        for finger in fingers:
                            avg_pos += finger.tip_position      
                        avg_pos /= len(fingers)
                        coords = avg_pos.to_tuple()
                        if coords[2] < 40:
                            self.xcor.append(coords[0])
                            self.ycor.append(coords[1])
                            print "Recorded X: %d, Y: %d" % (coords[0], coords[1])
            else:
                self.noin += 1
                if self.noin >= 100:
                    if self.state == 1:
                        self.xsav = self.xcor
                        self.ysav = self.ycor
                        self.xcor = []
                        self.ycor = []
                        print "Recording complete"
                        self.state = 3
                        self.wait = 0
                        self.noin = 0
                        self.paintCanvas.delete("all")
                    elif self.state == 2:
                        print "Signature complete"
                        diff = self.sigcomp()
                        print int(diff)
                        if diff > 50 or diff == -1:
                            print "You signature was not accepted, try again"
                            self.state = 3
                            self.wait = 0
                            self.noin = 0
                            self.xcor = []
                            self.ycor = []
                            self.paintCanvas.delete("all")
                        else:
                            print "Signature was accepted"
                            self.state = 0
                            self.paintCanvas.delete("all")
        elif self.state == 3:
            self.wait += 1
            w = 5 - int(self.wait/40)
            if w != self.lastwait:
                print "Signing in %d" % w
                self.lastwait = w
            if self.wait > 200:
                self.state = 2
                self.wait = 0
                self.paintCanvas.delete("all")
        elif self.state == 4:
            self.wait += 1
            w = 5 - int(self.wait/40)
            if w != self.lastwait:
                print "Recording in %d" % w
                self.lastwait = w
            if self.wait > 200:
                self.state = 1
                self.wait = 0
                self.paintCanvas.delete("all")

    def draw(self, x, y, width, height, color):
        self.paintCanvas.create_oval( x, y, x + width, y + height, fill = color, outline = "")

    def set_canvas(self, canvas):
        self.paintCanvas = canvas

    def rgb_to_hex(self, rgb):
        return '#%02x%02x%02x' % rgb

class PaintBox(Frame):

    def __init__( self ):
        Frame.__init__( self )
        self.leap = Leap.Controller()
        self.painter = SignatureListener()
        self.leap.add_listener(self.painter)
        self.pack( expand = YES, fill = BOTH )
        self.master.title( "Leap Signature" )
        self.master.geometry( "800x600" )

        # create Canvas component
        self.paintCanvas = Canvas( self, width = "800", height = "600" )
        self.paintCanvas.pack()
        self.painter.set_canvas(self.paintCanvas)

        self.painter.state = 0

def main():
    PaintBox().mainloop()

if __name__ == "__main__":
    main()