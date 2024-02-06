from drf_spectacular.utils import extend_schema_view, OpenApiParameter, extend_schema
from rest_framework import viewsets, status, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core import models
from recipe import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="tags",
                type=str,
                description="Comma separated list of tag IDs to filter",
            ),
            OpenApiParameter(
                name="ingredients",
                type=str,
                description="Comma separated list of ingredient IDs to filter",
            ),
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs"""

    serializer_class = serializers.RecipeDetailSerializer
    queryset = models.Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _params_to_ints(qs: str) -> list[int]:
        """Convert a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        # Filter by current user
        qs = self.queryset.filter(user=self.request.user)

        # Filter by tag query param
        tags = self.request.query_params.get("tags")
        if tags:
            tags_ids = self._params_to_ints(tags)
            qs = qs.filter(tags__id__in=tags_ids)

        # Filter by ingredient query param
        ingredients = self.request.query_params.get("ingredients")
        if ingredients:
            ingredients_ids = self._params_to_ints(ingredients)
            qs = qs.filter(ingredients__id__in=ingredients_ids)

        # Distinct is required due to inner join on tags/ingredients table
        qs = qs.order_by("-id").distinct()
        return qs

    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == "list":
            return serializers.RecipeSerializer
        elif self.action == "upload_image":
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)

    @action(methods=["POST"], detail=True, url_path="upload-image")
    def upload_image(self, request, pk=None):
        """Upload an image to recipe"""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "assigned_only",
                int,
                enum=[0, 1],
                description="Filter by items assigned to recipes.",
            )
        ]
    )
)
class BaseRecipeAttrViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Base viewset for recipe attributes"""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = self.queryset.filter(user=self.request.user)

        assigned_only = bool(int(self.request.query_params.get("assigned_only", 0)))
        if assigned_only:
            qs = qs.filter(recipe__isnull=False)

        return qs.order_by("-name").distinct()


class TagViewSet(BaseRecipeAttrViewSet):
    """View to manage tags"""

    serializer_class = serializers.TagSerializer
    queryset = models.Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    """View to manage ingredients"""

    serializer_class = serializers.IngredientSerializer
    queryset = models.Ingredient.objects.all()
