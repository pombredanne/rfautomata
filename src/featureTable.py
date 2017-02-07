'''
    This objected-oriented module defines a feature lookup table class

    This lookup table has two main purposes:
    1. We use the address spaces to efficiently fit all features into
    	as few STEs as possible.
    2. We use the resulting lookup table to map feature values to feature
    	labels.
    ----------------------
    Author: Tom Tracy II
    email: tjt7a@virginia.edu
    University of Virginia
    ----------------------
    18 November 2016
    Version 1.0
'''

# Utility imports
import copy
from termcolor import colored
from random import *
import math

# Define FeatureTable class
class FeatureTable(object):

	def __init__(self, features, threshold_map):

		# feature -> (STE, start, end)
		self.feature_pointer_ = {}

		# List of address spaces
		self.stes_ = []

		# Number of STES requires
		# Start with 1, then calculate correct number (post compact())
		self.ste_count_ = 1

		# A list of all features used
		self.features_ = features

		# A dictionary from features -> list of thresholds
		self.threshold_map_ = threshold_map

		flat_table_ = []

		# Iterate through all features
		for feature in self.features_:

			# Grab list of thresholds for the feature
			thresholds = self.threshold_map_[feature]

			# Concatenate to end of current address space
			start = len(flat_table_)
			end = start + len(thresholds)

			# Update pointers with (STE, Start index, end index)
			# This implies we are using only one STE (fine until we compact())
			self.feature_pointer_[feature] = (0, start, end)

			# Concatenate thresholds to flat table
			flat_table_ += thresholds

			# This is the end of the current feature
			flat_table_.append(-1)

		# For constructor cram all feature ranges into one STE
		self.stes_.append(flat_table_)

	# String representation of the STEs
	def __str__(self):
		string = ""

		# Enumerate all features and which STE its mapped to / what range
		for i, feature in enumerate(self.features_):
			ste, start, end = self.feature_pointer_[feature]
			string += colored("F:%d", 'magenta') % feature
			string += "STE:%d,S:%d,E:%d" % (ste, start, end)
			string += (";") if i != (len(self.features_) - 1) else ("\n\n")

		# Enumerate all stes
		for i, ste in enumerate(self.stes_):
			string += colored("STE:%d[", 'blue') % i

			# Enumerate all ranges
			for j, r in enumerate(ste):
				string += (colored(str(r), 'green') if r != -1 else colored(str(r), 'red'))
				string += "]"
				string += ("[") if j != len(ste) - 1 else colored("]", 'blue')

		return string

	# Return the range in the flat address space that corresponds to the start/end of a feature
	def get_range(self, feature):
		return self.feature_pointer_[feature]

	# Return the STE that this feature is mapped to
	def get_ste(self, feature):
		return get_range(feature)[0]

	# Return the tuple (ste, index) that represents the range in which the value is found
	# This is currently implemented with a linear-time algorithm, but can be
	# improved in the future
	def get_symbol(self, feature, value):

		# Grab the ste and the range of addresses assigned to feature
		ste, start, end = self.get_range(feature)

		for i in range(start, end + 1):

			threshold_value = self.stes_[ste][i]
			if threshold_value == -1 or threshold_value >= value:
				return (ste, i)
			else:
				continue

	# More complex compaction algorithm that deals features with many splits
	# Not looking to run a knapsack algorithm here
	#* This needs to further developed *#
	def compact2(self):

		self.ste_count_ = 1

		while True:

			# Keep incrementing the STE count
			self.ste_count_ += 1
			ste_index = 0

			# Zero the counters for the STEs
			temp_counts = [0 for x in range(self.ste_count_)]

			for feature in self.features_:

				if ste_index == self.ste_count_:
					ste_index = 0

				two_stes = False

				ste, start_index, end_index = self.get_range(feature)

				print "feature:%d, start_index:%d, end_index:%d" % (feature, start_index, end_index)

				range_size = (end_index - start_index) + 1

				# If the range for a particular feature is too big,
				# this compaction algorithm won't work
				if range_size > 254:

					# Break up this feature into multiple STEs
					# This feature needs two states
					if range_size > (254 ** 2):

						# We have WAY too many splits for this feature
						# To do: generalize it

						return -1

					# Ok, we'll handle this with two STEs
					else:

						range_size_msb = int(math.sqrt(range_size + 0.5))
						range_size_lsb = range_size_msb

						#OK, we need two STEs
						temp_counts[ste_index] += range_size_msb

						ste_index += 1

						ste_index = 0 if ste_index == ste_count_ else ste_index

						temp_counts[ste_index] += range_size_lsb

				else:
					temp_counts[ste_index(feature)] += range_size

				ste_index += 1

			if max(temp_counts) > 254:
				continue

			else:
				break

		print "Found minumum number of stes required to be: ", \
			self.ste_count_

		# Lambda expression for assigning ste_id based on feature
		# This is also true for naive!
		ste_index = lambda fid : fid % self.ste_count_

		# Empty the stes to fill with feature threshold ranges
		self.stes_ = [[] for x in range(self.ste_count_)]

		# Iterate over all features and fill STE namespaces
		for feature_index,feature in enumerate(self.features_):

			ste_i = ste_index(feature_index)
			thresholds = self.threshold_map_[feature]

			start = len(self.stes_[ste_i])
			end = start + len(thresholds)

			self.feature_pointer_[feature] = (ste_i, start, end)
			self.stes_[ste_i] +=  thresholds
			self.stes_[ste_i].append(-1)

	# Fit all ranges of all features in the minimum number of STEs
	def compact(self, naive=False):

		# This will set self.ste_count_
		if naive:

			for feature in self.features_:

				ste, start_index, end_index = self.get_range(feature)

				if ((end_index - start_index) + 1) > 254:
					print "Feature %d has too many splits! We don't support this yet" % feature
					exit()

			return_code = len(self.features_)

			print "Assigning one STE to each feature; %d STEs for %d features" % \
				(self.ste_count_, len(self.features_))

		else:
			return_code = self.calculate_min_stes()

		# Naive compaction failed
		if return_code == -1:
			if self.compact2() == -1:
				print "Sorry, we're railed"
				exit()
			else:
				print "Compact2() worked!"
				return 0

		else:
			self.ste_count_ = return_code

			print "Found minumum number of stes required to be: ", \
				self.ste_count_

			# Lambda expression for assigning ste_id based on feature
			ste_index = lambda fid : fid % self.ste_count_

			# Empty the stes to fill with feature threshold ranges
			self.stes_ = [[] for x in range(self.ste_count_)]

			# Iterate over all features and fill STE namespaces
			for feature_index,feature in enumerate(self.features_):

				ste_i = ste_index(feature_index)
				thresholds = self.threshold_map_[feature]

				start = len(self.stes_[ste_i])
				end = start + len(thresholds)

				self.feature_pointer_[feature] = (ste_i, start, end)
				self.stes_[ste_i] +=  thresholds
				self.stes_[ste_i].append(-1)

	'''
		For simplicity, we're making the assumption that all features
		have fewer than 254 thresholds; if this is not the case, this function
		and the compact() function need to be combined and extended.

		We use an assert to catch features that are too large
	'''

	# Calculate min STE count to fit all features; return number of stes needed
	def calculate_min_stes(self):

		# If max address space of all stes is <= 254 we good
		# This assumes that we've pushed all of the address spaces into
		# one STE to be split up into multiple
		if max(len(ste) for ste in self.stes_) <= 254:
			return 1

		else:
			ste_count_ = 1

			# Lambda expression for assigning ste_id based on feature
			ste_index = lambda fid, ste_count : fid % ste_count

			while True:

				# Keep incrementing the STE count
				ste_count_ += 1

				# Zero the counters for the STEs
				temp_counts = [0 for x in range(ste_count_)]

				for feature in self.features_:

					ste, start_index, end_index = self.get_range(feature)

					range_size = (end_index - start_index) + 1

					print "feature:%d, start_index:%d, end_index:%d" % (feature, start_index, end_index)

					# If the range for a particular feature is too big,
					# this compaction algorithm won't work
					if range_size > 254:
						return -1

					temp_counts[ste_index(feature, ste_count_)] += range_size

				if max(temp_counts) > 254:
					continue

				else:
					return ste_count_
