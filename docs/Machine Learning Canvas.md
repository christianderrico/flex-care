# Machine Learning Canvas

![MLCanvas](https://madewithml.com/static/images/mlops/design/ml_canvas.png)
**Article**: Goku Mohandas. Product - Made With ML. 2023. [Link](https://madewithml.com/courses/mlops/product-design/)

## Background

Set the scene for what we're trying to do through a user-centric approach:

- **users**: profile/persona of our users
- **goals**: our users' main goals
- **pains**: obstacles preventing our users from achieving their goals

## Value proposition

Propose the value we can create through a product-centric approach:

- **product**: what needs to be built to help our users reach their goals?
- **alleviate**: how will the product reduce pains?
- **advantages**: how will the product create gains?

## Objectives

Breakdown the product into key objectives that we want to focus on.

## Solution

Describe the solution required to meet our objectives, including its:

- **core features**: key features that will be developed;
- **integration**: how the product will integrate with other services;
- **alternatives**: alternative solutions that we should considered;
- **constraints**: limitations that we need to be aware of;
- **out-of-scope**: features that we will not be developing for now.

## Feasibility

How feasible is our solution and do we have the required resources to deliver it (data, funding, team, etc.)?

## Data

Describe the training and production (batches/streams) sources of data.

## Labeling

Describe the labeling process (ingestions, QA, etc.) and how we decided on the features and labels.

## Metrics

One of the hardest challenges with ML systems is tying our core objectives, many of which may be qualitative, with quantitative metrics that our model can optimize towards.

## Evaluation

Once we have our metrics defined, we need to think about when and how we'll evaluate our model.

### Offline evaluation

Offline evaluation requires a gold standard holdout dataset that we can use to benchmark all of our models.

### Online evaluation

Online evaluation ensures that our model continues to perform well in production and can be performed using labels or, in the event we don't readily have labels, proxy signals.
It's important that we measure real-time performance before committing to replace our existing version of the system.

- Internal canary rollout, monitoring for proxy/actual performance, etc.;
- Rollout to the larger internal team for more feedback;
- A/B rollout to a subset of the population to better understand UX, utility, etc.;

## Modeling

While the specific methodology we employ can differ based on the problem, there are core principles we always want to follow:

- **End-to-end utility**: the end result from every iteration should deliver minimum end-to-end utility so that we can benchmark iterations against each other and plug-and-play with the system.
- **Manual before ML**: try to see how well a simple rule-based system performs before moving onto more complex ones.
- **Augment vs. automate**: allow the system to supplement the decision-making process as opposed to making the actual decision.
- **Internal vs. external**: not all early releases have to be end-user facing. We can use early versions for internal validation, feedback, data collection, etc.
- **Thorough**: every approach needs to be well tested (code, data + models) and evaluated, so we can objectively benchmark different approaches.

## Inference

Once we have a model we're satisfied with, we need to think about whether we want to perform batch (offline) or real-time (online) inference.

**Batch inference**

We can use our models to make batch predictions on a finite set of inputs which are then written to a database for low latency inference. When a user or downstream service makes an inference request, cached results from the database are returned. In this scenario, our trained model can directly be loaded and used for inference in the code. It doesn't have to be served as a separate service.

**Online inference**

We can also serve real-time predictions where input features are fed to the model to retrieve predictions. In this scenario, our model will need to be served as a separate service (ex. api endpoint) that can handle incoming requests.

## Feedback

How do we receive feedback on our system and incorporate it into the next iteration? This can involve both human-in-the-loop feedback as well as automatic feedback via monitoring, etc.