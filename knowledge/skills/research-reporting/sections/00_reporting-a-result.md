# Reporting a result so it can be checked

A result that cannot be checked is not a result. This note is what to put around a number
before it goes into an answer.

## Say what kind of thing each number is

Every number in an answer is one of four things, and the reader must be able to tell which
without asking.

| Kind | Where it came from | Marker |
| --- | --- | --- |
| Computed | A run_model call in this conversation | [model:name@version] |
| Measured | A reference dataset queried in this conversation | [data:slug] |
| Reported | A section of a paper you read | [slug#id] |
| Yours | Arithmetic you did on the above | no marker, and say so |

Never let a computed number and a measured one sit in the same sentence without saying
which is which. A simulation agreeing with an observation is a claim about the model; the
same sentence with the two swapped is a claim about the world.

## Report the configuration with the number

A brightness temperature without a frequency is not an answer. State, at minimum, the
observable, the sensor configuration, and the parameters the question was about. If a value
came from a sweep, give the range swept and the number of points, not only the endpoints.

## Say what the model cannot tell you

Three limits are worth stating whenever they apply.

- **Validity**: a run near the edge of a declared range is weaker evidence than one in the
  middle, and the declaration says where the edges are.
- **Idealisation**: every bundled model here is a single homogeneous layer. Real snow is
  stratified, real soil has a roughness spectrum, and a single-layer answer is a first-order
  answer.
- **What was assumed**: the parameters you chose rather than were given, from the planning
  step, belong in the answer, not only in your reasoning.

## Report a null result as a result

"The corpus does not cover this", "the model declares this outside its range", and "the two
runs are not comparable" are answers. They are more useful than a number produced by
quietly relaxing the question, because the reader can act on them. Lead with the null result
rather than burying it after a paragraph of what you could do instead.

## Do not restate what is already on screen

A chart is already showing its values. Repeating the series point by point in prose adds
nothing a reader can use and invites transcription errors. Describe the shape, name the
turning points that matter, and let the figure carry the numbers.
