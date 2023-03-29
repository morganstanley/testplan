"""Module containing environments related classes."""

from testplan.common.entity import Resource, Environment


class EnvironmentCreator:
    """
    Environment creator interface.
    """

    def __init__(self, uid, resources=None):
        self._uid = uid
        self._resources = resources or []

    def add_resource(self, resource):
        """
        Add a resource to the future created environment.
        """
        raise NotImplementedError

    def uid(self):
        """
        Environment uid.
        """
        return self._uid

    def create(self, parent):
        """
        Create a new environment containing added resources.
        """
        raise NotImplementedError


class LocalEnvironment(EnvironmentCreator):
    """
    Creator class of a local environment.
    """

    def add_resource(self, resource):
        """
        Add a resource to the future created environment.
        """
        if any(obj.uid() == resource.uid() for obj in self._resources):
            raise RuntimeError(
                "Resource with uid {} already exists.".format(resource.uid())
            )
        self._resources.append(resource)

    def create(self, parent):
        """
        Create a new environment containing added resources.
        """
        env = Environment(parent=parent)
        for item in self._resources:
            env.add(item)
        return env


class Environments(Resource):
    """
    Environments holder resource.

    Also inherits all
    :py:class:`~testplan.common.entity.base.Resource` options.
    """

    def __init__(self, **options):
        super(Environments, self).__init__(**options)
        self._envs = {}

    @property
    def envs(self):
        """
        Returns all added environments.
        """
        return self._envs

    def __getattr__(self, item):
        try:
            return self.__getattribute__(item)
        except AttributeError:
            try:
                return self._envs[item]
            except KeyError:
                # raise AttributeError so that below still works:
                # getattr(env, "some_attr", "default_value")
                raise AttributeError

    def __getitem__(self, item):
        return self._envs[item]

    def delete(self, uid):
        """Delete an environment."""
        del self._envs[uid]

    def add(self, env, uid):
        """Add an environment."""
        if uid in self._envs:
            raise ValueError("{} already exists.".format(uid))
        self._envs[uid] = env

    def starting(self):
        """Start all added environments."""
        for uid in self._envs:
            self._envs[uid].start()

    def stopping(self):
        """Stop all added environments."""
        for uid in self._envs:
            self._envs[uid].stop()

    def abort_dependencies(self):
        """Abort all resources on all environments."""
        for env in self._envs.values():
            for resource in env:
                yield resource

    def aborting(self):
        """Abort logic."""
        pass
