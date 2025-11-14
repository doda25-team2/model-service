# SMS Checker Backend

To start the SMS-checker back-end server up, after having cloned this reporistory and navigated to the root directory:


```bash
docker build -t model-service .
docker run -d -p 8081:8081 model-service
```

The server will start on port 8081.
Once its startup has finished, you can either access [localhost:8081/apidocs](http://localhost:8081/apidocs) in your browser to interact with the service, or you send `POST` requests to request predictions, for example with `curl`:

```bash
    $ curl -X POST "http://localhost:8081/predict" -H "Content-Type: application/json" -d '{"sms": "test ..."}'

    {
      "classifier": "decision tree",
      "result": "ham",
      "sms": "test ..."
    }
```
