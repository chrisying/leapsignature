################################################################################
# Copyright (C) 2012-2013 Leap Motion, Inc. All rights reserved.               #
# Leap Motion proprietary and confidential. Not for distribution.              #
# Use subject to the terms of the Leap Motion SDK Agreement available at       #
# https://developer.leapmotion.com/sdk_agreement, or another agreement         #
# between Leap Motion and you, your company or other organization.             #
################################################################################

#Signature recogition code
#Chris Ying 2013

import Leap, sys


class SignatureListener(Leap.Listener):

	state = 0 # default = 0, recording = 1, saving = 2, wait = 3, exit = -1
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

	def on_disconnect(self, controller):
		# Note: not dispatched when running in a debugger.
		print "Disconnected"

	def on_exit(self, controller):
		print "Exited"

	def on_frame(self, controller):
		# Get the most recent frame and report some basic information
		frame = controller.frame()
		if self.state == 1 or self.state == 2: #recording state
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
						else:
							print "Signature was accepted"
							raw_input()
		if self.state == 3:
			self.wait += 1
			w = 5 - int(self.wait/40)
			if w != self.lastwait:
				print "Signing in %d" % w
				self.lastwait = w
			if self.wait > 200:
				self.state = 2
				self.wait = 0


def main():
	# Create a sample listener and controller
	listener = SignatureListener()
	controller = Leap.Controller()

	# Have the sample listener receive events from the controller
	controller.add_listener(listener)

	# Keep this process running until Enter is pressed
	while listener.state != -1:
		s = sys.stdin.readline()
		if s == "\n":
			listener.state = 1
		if s == "quit\n":
			break
		pass

	# Remove the sample listener when done
	controller.remove_listener(listener)


if __name__ == "__main__":
	main()
